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
        # Extract database session from kwargs
        db = kwargs.get("db")
        if not db or not isinstance(db, Session):
            # If no db session, just call the original function
            logger.warning("No database session found, skipping cache")
            return func(*args, **kwargs)
        
        # Generate cache key from function arguments
        cache_key = generate_cache_key(*args, **kwargs)
        
        # Check if we have a recent cached result
        cached_result = get_cached_chart(db, cache_key)
        if cached_result:
            logger.info("Cache hit", extra={"cache_key": cache_key})
            return cached_result
        
        # Call the original function
        result = func(*args, **kwargs)
        
        # Store result in cache
        try:
            store_chart_result(db, cache_key, result)
            logger.info("Cached calculation result", extra={"cache_key": cache_key})
        except Exception as e:
            logger.error("Failed to cache result", extra={"error": str(e)})
        
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
    
    # Query for cached calculation
    cached = db.query(ChartCalculation).filter(
        ChartCalculation.cache_key == cache_key,
        ChartCalculation.calculation_timestamp >= min_timestamp
    ).first()
    
    if not cached or not cached.result_json:
        return None
    
    try:
        return json.loads(cached.result_json)
    except json.JSONDecodeError:
        logger.error("Failed to decode cached result", extra={"cache_key": cache_key})
        return None

def store_chart_result(db: Session, cache_key: str, result: Any) -> None:
    """
    Store a chart calculation result in the cache
    
    Args:
        db: Database session
        cache_key: Cache key
        result: Calculation result to cache
    """
    # Serialize result to JSON
    result_json = json.dumps(result)
    
    # Check if we already have an entry for this key
    existing = db.query(ChartCalculation).filter(
        ChartCalculation.cache_key == cache_key
    ).first()
    
    timestamp = datetime.utcnow().isoformat()
    
    if existing:
        # Update existing entry
        existing.result_json = result_json
        existing.calculation_timestamp = timestamp
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
    
    db.commit()