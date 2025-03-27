"""
Redis caching utilities for expensive calculations
"""
import json
import logging
import os
from datetime import timedelta
from typing import Any, Dict, Optional, Union

import redis
from redis.exceptions import RedisError

# Configure logger
logger = logging.getLogger(__name__)

# Get Redis connection details from environment variables
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_CACHE_TTL = int(os.environ.get("REDIS_CACHE_TTL", 604800))  # Default: 7 days in seconds

# Create a Redis connection pool
try:
    redis_pool = redis.ConnectionPool.from_url(
        REDIS_URL, 
        max_connections=10,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True
    )
    logger.info(f"Redis connection pool initialized with URL: {REDIS_URL.split('@')[-1]}")
except Exception as e:
    logger.error(f"Failed to initialize Redis connection pool: {str(e)}")
    redis_pool = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get a Redis client from the connection pool
    
    Returns:
        Redis client or None if connection pool initialization failed
    """
    if redis_pool is None:
        logger.warning("Redis connection pool is not available")
        return None
    
    return redis.Redis(connection_pool=redis_pool)


def set_cache(key: str, data: Any, expire_time: Optional[int] = None) -> bool:
    """
    Store data in Redis cache
    
    Args:
        key: Cache key
        data: Data to store (will be JSON serialized)
        expire_time: Time to live in seconds (defaults to REDIS_CACHE_TTL)
        
    Returns:
        bool: True if successfully stored, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    
    if expire_time is None:
        expire_time = REDIS_CACHE_TTL
    
    try:
        # Serialize the data to JSON
        serialized_data = json.dumps(data)
        
        # Store in Redis with expiration
        client.set(key, serialized_data, ex=expire_time)
        
        logger.debug(f"Cached data with key: {key}, TTL: {expire_time}s")
        return True
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization error for key {key}: {str(e)}")
        return False
    except RedisError as e:
        logger.error(f"Redis error while setting cache for key {key}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while setting cache for key {key}: {str(e)}")
        return False


def get_cache(key: str) -> Optional[Any]:
    """
    Retrieve data from Redis cache
    
    Args:
        key: Cache key to look up
        
    Returns:
        Cached data or None if not found/error
    """
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        # Retrieve from Redis
        data = client.get(key)
        
        if data is None:
            logger.debug(f"Cache miss for key: {key}")
            return None
        
        # Deserialize the JSON data
        result = json.loads(data)
        
        logger.debug(f"Cache hit for key: {key}")
        return result
    except RedisError as e:
        logger.error(f"Redis error while getting cache for key {key}: {str(e)}")
        return None
    except (TypeError, ValueError) as e:
        logger.error(f"JSON deserialization error for key {key}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while getting cache for key {key}: {str(e)}")
        return None


def delete_cache(key: str) -> bool:
    """
    Delete data from Redis cache
    
    Args:
        key: Cache key to delete
        
    Returns:
        bool: True if successfully deleted, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        # Delete from Redis
        result = client.delete(key)
        
        if result > 0:
            logger.debug(f"Deleted cache for key: {key}")
            return True
        else:
            logger.debug(f"No cache found for deletion with key: {key}")
            return False
    except RedisError as e:
        logger.error(f"Redis error while deleting cache for key {key}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while deleting cache for key {key}: {str(e)}")
        return False


def flush_cache() -> bool:
    """
    Flush all data from Redis cache
    
    Returns:
        bool: True if successfully flushed, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.flushdb()
        logger.info("Redis cache flushed")
        return True
    except RedisError as e:
        logger.error(f"Redis error while flushing cache: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while flushing cache: {str(e)}")
        return False


def generate_cache_key(*args: Any, **kwargs: Any) -> str:
    """
    Generate a unique cache key based on function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    import hashlib
    
    # Convert args and kwargs to a string representation
    key_parts = []
    
    # Add positional args
    for arg in args:
        key_parts.append(str(arg))
    
    # Add keyword args, sorted by key to ensure consistency
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}:{kwargs[k]}")
    
    # Join parts and hash
    key_string = ":".join(key_parts)
    hashed_key = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"astro_chart:{hashed_key}"


def redis_cache_decorator(expire_time: Optional[int] = None):
    """
    Decorator to cache function results in Redis
    
    Args:
        expire_time: Cache TTL in seconds, defaults to REDIS_CACHE_TTL
        
    Returns:
        Wrapped function with Redis caching
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key based on function name and arguments
            cache_key = f"{func.__module__}.{func.__name__}:" + generate_cache_key(*args, **kwargs)
            
            # Try to get cached result
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                # Add cache metadata
                if isinstance(cached_result, dict):
                    cached_result["_cache_hit"] = True
                logger.info(f"Cache hit for {func.__name__} with key {cache_key}")
                return cached_result
            
            # Cache miss, execute the function
            logger.info(f"Cache miss for {func.__name__} with key {cache_key}")
            result = func(*args, **kwargs)
            
            # Store the result in cache
            if result is not None:
                # Add cache metadata to dict results
                if isinstance(result, dict):
                    result["_cache_hit"] = False
                set_cache(cache_key, result, expire_time)
            
            return result
        return wrapper
    return decorator


def is_redis_available() -> bool:
    """
    Check if Redis is available
    
    Returns:
        bool: True if Redis is available, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        return client.ping()
    except Exception:
        return False