"""
Caching utilities for expensive calculations
"""
import json
import hashlib
from typing import Any, Dict, Optional, Callable, TypeVar
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy.orm import Session

from app.models import ChartCalculation
from app.utils.logging import get_logger

# Type variables for generic function signatures
T = TypeVar('T')
R = TypeVar('R')

# Set up logger
logger = get_logger(__name__)

def generate_cache_key(*args: Any, **kwargs: Any) -> str:
    """
    Generate a unique cache key based on function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        SHA-256 hash of the serialized arguments
    """
    # Create a dictionary of all arguments
    key_dict = {
        "args": args,
        "kwargs": {k: v for k, v in kwargs.items() if k != "db"}
    }
    
    # Convert to a stable JSON string and hash it
    key_str = json.dumps(key_dict, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()

def cache_chart_calculation(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator to cache chart calculation results in the database
    
    Args:
        func: Function to cache
        
    Returns:
        Wrapped function with caching
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        import time
        
        # Extract database session from kwargs
        db = kwargs.get("db")
        if not db or not isinstance(db, Session):
            # If no db session, just call the original function
            logger.warning("No database session found, skipping cache")
            return func(*args, **kwargs)
        
        # Generate cache key from function arguments
        start_time = time.time()
        cache_key = generate_cache_key(*args, **kwargs)
        
        # Track performance metrics
        perf_metrics = {
            "cache_key_gen_time": round((time.time() - start_time) * 1000, 2)  # ms
        }
        
        # Check if we have a recent cached result
        cache_lookup_start = time.time()
        cached_result = get_cached_chart(db, cache_key)
        perf_metrics["cache_lookup_time"] = round((time.time() - cache_lookup_start) * 1000, 2)  # ms
        
        if cached_result:
            logger.info("Cache hit", extra={
                "cache_key": cache_key,
                "perf_metrics": perf_metrics
            })
            return cached_result
        
        # Call the original function if cache miss
        logger.info("Cache miss, executing calculation", extra={"cache_key": cache_key})
        calc_start = time.time()
        result = func(*args, **kwargs)
        calc_time = round((time.time() - calc_start) * 1000, 2)  # ms
        perf_metrics["calculation_time"] = calc_time
        
        # Store result in cache if calculation took more than 100ms
        # This prevents caching trivial calculations
        if calc_time > 100:  # Only cache if calculation was non-trivial
            cache_store_start = time.time()
            success = store_chart_result(db, cache_key, result)
            perf_metrics["cache_store_time"] = round((time.time() - cache_store_start) * 1000, 2)  # ms
            
            if success:
                logger.info("Cached calculation result", extra={
                    "cache_key": cache_key,
                    "perf_metrics": perf_metrics
                })
            else:
                logger.warning("Failed to cache result", extra={
                    "cache_key": cache_key,
                    "perf_metrics": perf_metrics
                })
        else:
            logger.debug("Skipped caching fast calculation", extra={
                "cache_key": cache_key,
                "calc_time_ms": calc_time
            })
        
        # Track overall performance
        perf_metrics["total_time"] = round((time.time() - start_time) * 1000, 2)  # ms
        logger.debug("Performance metrics", extra={"perf_metrics": perf_metrics})
        
        return result
    
    return wrapper

def get_cached_chart(db: Session, cache_key: str, max_age: timedelta = timedelta(days=7)) -> Optional[Dict[str, Any]]:
    """
    Retrieve a cached chart result if available and not expired
    
    Args:
        db: Database session
        cache_key: Cache key to look up
        max_age: Maximum age of cached result
        
    Returns:
        Cached chart data or None if not found/expired
    """
    # Calculate the earliest acceptable timestamp
    min_timestamp = (datetime.utcnow() - max_age).isoformat()
    
    try:
        # Use more efficient querying with proper error handling
        cached = db.query(ChartCalculation).filter(
            ChartCalculation.cache_key == cache_key,
            ChartCalculation.calculation_timestamp >= min_timestamp
        ).first()
        
        if not cached or not cached.result_json:
            logger.debug("Cache miss", extra={"cache_key": cache_key})
            return None
        
        # Attempt to decode the JSON with error handling
        try:
            result = json.loads(cached.result_json)
            # Add a cache status flag for debugging purposes
            if isinstance(result, dict):
                result["_cache_status"] = {
                    "from_cache": True,
                    "cache_timestamp": cached.calculation_timestamp,
                    "cache_key": cache_key[:8] + "..." # Show only first 8 chars for brevity
                }
            return result
        except json.JSONDecodeError as e:
            logger.error("Failed to decode cached result", extra={
                "cache_key": cache_key,
                "error": str(e),
                "json_start": cached.result_json[:100] if cached.result_json else "None"
            })
            # Delete corrupted cache entry to prevent future issues
            db.delete(cached)
            db.commit()
            return None
    except Exception as e:
        # Catch any database errors and log them
        logger.error("Error retrieving from cache", extra={
            "cache_key": cache_key,
            "error": str(e)
        })
        return None

def store_chart_result(db: Session, cache_key: str, result: Any) -> bool:
    """
    Store a chart calculation result in the cache
    
    Args:
        db: Database session
        cache_key: Cache key
        result: Calculation result to cache
        
    Returns:
        bool: True if successfully stored, False otherwise
    """
    try:
        # Remove any cache status info before storing
        if isinstance(result, dict) and "_cache_status" in result:
            # Create a copy to avoid modifying the original
            result_copy = result.copy()
            del result_copy["_cache_status"]
            result_to_store = result_copy
        else:
            result_to_store = result
            
        # Serialize result to JSON
        result_json = json.dumps(result_to_store)
        
        # Create a transaction - which will be rolled back if any exceptions occur
        try:
            # Check if we already have an entry for this key using a more efficient query
            # that only fetches the ID rather than the entire row
            existing_id = db.query(ChartCalculation.id).filter(
                ChartCalculation.cache_key == cache_key
            ).scalar()
            
            timestamp = datetime.utcnow().isoformat()
            
            if existing_id:
                # Update existing entry directly using the ID, more efficient
                db.query(ChartCalculation).filter(
                    ChartCalculation.id == existing_id
                ).update({
                    "result_json": result_json,
                    "calculation_timestamp": timestamp
                })
            else:
                # Create new entry
                # Note: We set other required fields to placeholders since they're 
                # redundant (the real data is in the cache key)
                new_cache = ChartCalculation(
                    cache_key=cache_key,
                    result_json=result_json,
                    birth_date="cache",
                    birth_time="cache",
                    latitude=0.0,
                    longitude=0.0,
                    timezone="cache",
                    calculation_timestamp=timestamp
                )
                db.add(new_cache)
            
            # Commit the transaction
            db.commit()
            return True
            
        except Exception as e:
            # Rollback on any errors
            db.rollback()
            raise e
            
    except Exception as e:
        logger.error("Failed to store chart result in cache", extra={
            "cache_key": cache_key,
            "error": str(e),
            "error_type": type(e).__name__
        })
        return False