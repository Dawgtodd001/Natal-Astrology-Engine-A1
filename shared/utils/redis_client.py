"""
Redis client utilities for caching and message broker services
"""
import os
import json
import time
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union
from functools import wraps

# Redis connection
try:
    import redis
    from redis import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Import settings
from shared.config.settings import settings

# Create logger
logger = logging.getLogger(__name__)

# Global Redis connection pool
_connection_pool = None
_client_instance = None


def get_cache_key(prefix: str, **kwargs) -> str:
    """
    Generate a cache key based on parameters
    
    Args:
        prefix: Prefix for the key to identify the type of data
        **kwargs: Key-value parameters used to generate the key
        
    Returns:
        A unique cache key string
    """
    # Sort kwargs by key to ensure consistent key generation
    sorted_items = sorted(kwargs.items())
    
    # Create string representation of parameters
    param_str = "&".join([f"{k}={v}" for k, v in sorted_items])
    
    # Hash the parameters for shorter keys
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    
    return f"{prefix}:{param_hash}"


def init_redis_connection_pool() -> Optional[ConnectionPool]:
    """
    Initialize Redis connection pool
    
    Returns:
        Redis connection pool or None if Redis is not available
    """
    global _connection_pool
    
    if not REDIS_AVAILABLE:
        logger.warning("Redis package not installed - caching and async tasks will not be available")
        return None
    
    try:
        # If connection pool already exists, return it
        if _connection_pool is not None:
            return _connection_pool
            
        # Get Redis URL from settings
        redis_url = settings.REDIS_URL
        
        # Create and return connection pool
        _connection_pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW,
            socket_timeout=2.0,
            socket_keepalive=True,
            socket_connect_timeout=1.0,
            health_check_interval=30,
        )
        
        logger.info(f"Redis connection pool initialized with URL: {redis_url}")
        return _connection_pool
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis connection pool: {str(e)}")
        return None


def get_redis_client() -> Optional[Any]:
    """
    Get Redis client with connection pooling
    
    Returns:
        Redis client or None if Redis is not available
    """
    global _client_instance
    
    # Return existing instance if available
    if _client_instance is not None:
        return _client_instance
        
    # Initialize connection pool
    pool = init_redis_connection_pool()
    
    if pool is None:
        return None
        
    try:
        # Create client from pool
        _client_instance = redis.Redis(connection_pool=pool, decode_responses=True)
        
        # Test connection with ping
        _client_instance.ping()
        logger.info("Redis client initialized successfully")
        
        return _client_instance
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {str(e)}")
        return None


def is_redis_available() -> bool:
    """
    Check if Redis is available
    
    Returns:
        True if Redis is available, False otherwise
    """
    try:
        client = get_redis_client()
        if client is None:
            return False
            
        # Test connection
        return client.ping()
        
    except Exception:
        return False


def flush_cache() -> bool:
    """
    Flush all cache data
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis_client()
        if client is None:
            return False
            
        # Flush all data
        client.flushdb()
        logger.info("Redis cache flushed")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to flush Redis cache: {str(e)}")
        return False


def cache_get(
    key: str, 
    default: Any = None, 
    cache_type: str = "default"
) -> Any:
    """
    Get a value from Redis cache with metrics tracking
    
    Args:
        key: Cache key
        default: Default value to return if key not found
        cache_type: Type of cache for metrics
        
    Returns:
        Cached value or default if not found
    """
    start_time = time.time()
    client = get_redis_client()
    
    # If Redis is not available, return default
    if client is None:
        return default
        
    try:
        # Get value from cache
        value = client.get(key)
        
        # Track metrics
        from shared.monitoring.metrics import track_cache_operation
        elapsed = time.time() - start_time
        
        if value is not None:
            # Value found in cache
            track_cache_operation(cache_type, "hit", elapsed)
            
            # Try to parse JSON
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                # Return raw value if not JSON
                return value
        else:
            # Value not found in cache
            track_cache_operation(cache_type, "miss", elapsed)
            return default
            
    except Exception as e:
        logger.error(f"Error getting value from cache: {str(e)}")
        return default


def cache_set(
    key: str, 
    value: Any, 
    ttl: Optional[int] = None, 
    cache_type: str = "default"
) -> bool:
    """
    Set a value in Redis cache with metrics tracking
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (optional)
        cache_type: Type of cache for metrics
        
    Returns:
        True if successful, False otherwise
    """
    start_time = time.time()
    client = get_redis_client()
    
    # If Redis is not available, return False
    if client is None:
        return False
        
    try:
        # Convert value to JSON if it's a dict, list, or other complex type
        if isinstance(value, (dict, list, tuple, set, bool)) or value is None:
            value_str = json.dumps(value)
        else:
            value_str = str(value)
            
        # Set value in cache
        if ttl:
            result = client.setex(key, ttl, value_str)
        else:
            result = client.set(key, value_str)
            
        # Track metrics
        from shared.monitoring.metrics import track_cache_operation
        elapsed = time.time() - start_time
        track_cache_operation(cache_type, "set", elapsed)
        
        return result
        
    except Exception as e:
        logger.error(f"Error setting value in cache: {str(e)}")
        return False


def cache_delete(key: str) -> bool:
    """
    Delete a value from Redis cache
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    client = get_redis_client()
    
    # If Redis is not available, return False
    if client is None:
        return False
        
    try:
        # Delete key from cache
        result = client.delete(key)
        return result > 0
        
    except Exception as e:
        logger.error(f"Error deleting key from cache: {str(e)}")
        return False


def get_cache_keys(pattern: str = "*") -> List[str]:
    """
    Get all keys matching a pattern
    
    Args:
        pattern: Pattern to match
        
    Returns:
        List of keys
    """
    client = get_redis_client()
    
    # If Redis is not available, return empty list
    if client is None:
        return []
        
    try:
        # Get keys matching pattern
        return client.keys(pattern)
        
    except Exception as e:
        logger.error(f"Error getting cache keys: {str(e)}")
        return []


def get_cache_stats() -> Dict[str, Any]:
    """
    Get Redis cache statistics
    
    Returns:
        Dictionary of cache statistics
    """
    client = get_redis_client()
    
    # If Redis is not available, return empty dict
    if client is None:
        return {"available": False}
        
    try:
        # Get server info
        info = client.info()
        
        # Build statistics
        stats = {
            "available": True,
            "keys": client.dbsize(),
            "memory_used": info.get("used_memory_human", "Unknown"),
            "clients_connected": info.get("connected_clients", 0),
            "uptime_days": round(int(info.get("uptime_in_seconds", 0)) / 86400, 2),
            "version": info.get("redis_version", "Unknown"),
            "hits": int(info.get("keyspace_hits", 0)),
            "misses": int(info.get("keyspace_misses", 0)),
        }
        
        # Calculate hit rate if both hits and misses are non-zero
        total_requests = stats["hits"] + stats["misses"]
        stats["hit_rate"] = round(stats["hits"] / total_requests * 100, 2) if total_requests > 0 else 0
        
        # Add keyspace info
        db_keys = {}
        for key in info:
            if key.startswith("db"):
                db_keys[key] = info[key]
                
        stats["keyspace"] = db_keys
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting cache statistics: {str(e)}")
        return {"available": False, "error": str(e)}


def cached(
    ttl: int = 3600, 
    prefix: str = "", 
    cache_type: str = "function", 
    cache_null: bool = False
):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        prefix: Key prefix
        cache_type: Type of cache for metrics
        cache_null: Whether to cache None results
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key based on function name, args, and kwargs
            key_prefix = prefix if prefix else f"cached:{func.__module__}:{func.__name__}"
            
            # Extract cache key parameters from kwargs, fall back to args if needed
            # We need to convert args to serializable values for the cache key generation
            key_args = {f"arg{i}": str(arg) for i, arg in enumerate(args)}
            key_kwargs = {k: str(v) for k, v in kwargs.items()}
            key_params = {**key_args, **key_kwargs}
            
            cache_key = get_cache_key(key_prefix, **key_params)
            
            # Try to get from cache first
            cached_value = cache_get(cache_key, cache_type=cache_type)
            
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
                
            # If not in cache, call function
            result = func(*args, **kwargs)
            
            # Cache the result if it's not None or if cache_null is True
            if result is not None or cache_null:
                cache_set(cache_key, result, ttl=ttl, cache_type=cache_type)
                
            return result
            
        return wrapper
        
    return decorator