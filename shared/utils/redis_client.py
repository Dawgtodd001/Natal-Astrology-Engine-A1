"""
Redis client utility for microservices.

This module provides a shared Redis client implementation
that can be used across all microservices for caching and
message brokering.
"""

import os
import logging
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse
import json

# Attempt to import Redis
try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Set up logger
logger = logging.getLogger(__name__)

# Global connection pool
_redis_connection_pool = None


def get_redis_client() -> Optional['redis.Redis']:
    """
    Get a Redis client with connection pooling.
    
    Returns:
        Redis client object or None if Redis is not available
        
    Note:
        Connection pooling is used to efficiently reuse connections
        across multiple requests, which is important for performance.
    """
    global _redis_connection_pool
    
    if not REDIS_AVAILABLE:
        logger.warning("Redis package is not installed")
        return None
    
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    try:
        # Initialize connection pool if needed
        if _redis_connection_pool is None:
            parsed_url = urlparse(redis_url)
            
            # Extract password if present
            password = None
            if "@" in parsed_url.netloc:
                _, credential_part = parsed_url.netloc.split("@", 1)
                if ":" in credential_part:
                    password = credential_part.split(":", 1)[1]
            
            # Determine database number
            db = 0
            if parsed_url.path and len(parsed_url.path) > 1:
                try:
                    db = int(parsed_url.path.lstrip("/"))
                except ValueError:
                    logger.warning(f"Invalid Redis DB number in URL path: {parsed_url.path}")
            
            # Create connection pool
            _redis_connection_pool = ConnectionPool.from_url(
                redis_url,
                decode_responses=False,  # Keep binary data as is
                max_connections=10,      # Adjust based on needs
                socket_timeout=2.0,      # Timeout for connections
                socket_keepalive=True    # Keep connections alive
            )
            logger.debug(f"Redis connection pool created for {redis_url}")
        
        # Create client using the pool
        client = redis.Redis(connection_pool=_redis_connection_pool)
        
        # Test connection
        client.ping()
        return client
    
    except redis.exceptions.RedisError as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error connecting to Redis: {e}")
        return None


def cache_get(key: str, cache_type: str = "default") -> Optional[bytes]:
    """
    Get a value from Redis cache with metrics tracking.
    
    Args:
        key: Cache key
        cache_type: Type of cache for metrics
        
    Returns:
        Cached value (bytes) or None if not found
    """
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        value = client.get(key)
        
        # Import here to avoid circular imports
        from shared.monitoring.prometheus import track_cache_operation
        
        # Track metrics
        track_cache_operation(
            cache_type=cache_type,
            hit=value is not None,
            service="shared"
        )
        
        return value
    except Exception as e:
        logger.warning(f"Error getting key '{key}' from Redis: {e}")
        return None


def cache_set(key: str, value: bytes, ttl: Optional[int] = None, cache_type: str = "default") -> bool:
    """
    Set a value in Redis cache with metrics tracking.
    
    Args:
        key: Cache key
        value: Value to cache (bytes)
        ttl: Time to live in seconds (optional)
        cache_type: Type of cache for metrics
        
    Returns:
        True if successful, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        if ttl is not None:
            result = client.setex(key, ttl, value)
        else:
            result = client.set(key, value)
        
        return bool(result)
    except Exception as e:
        logger.warning(f"Error setting key '{key}' in Redis: {e}")
        return False


def cache_delete(key: str) -> bool:
    """
    Delete a value from Redis cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        result = client.delete(key)
        return bool(result)
    except Exception as e:
        logger.warning(f"Error deleting key '{key}' from Redis: {e}")
        return False


def cache_get_json(key: str, cache_type: str = "default") -> Optional[Any]:
    """
    Get a JSON value from Redis cache.
    
    Args:
        key: Cache key
        cache_type: Type of cache for metrics
        
    Returns:
        Deserialized JSON value or None if not found
    """
    data = cache_get(key, cache_type)
    if data is None:
        return None
    
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        logger.warning(f"Failed to decode JSON from Redis key '{key}'")
        return None


def cache_set_json(key: str, value: Any, ttl: Optional[int] = None, cache_type: str = "default") -> bool:
    """
    Set a JSON value in Redis cache.
    
    Args:
        key: Cache key
        value: Python object to serialize and cache
        ttl: Time to live in seconds (optional)
        cache_type: Type of cache for metrics
        
    Returns:
        True if successful, False otherwise
    """
    try:
        json_data = json.dumps(value).encode('utf-8')
        return cache_set(key, json_data, ttl, cache_type)
    except TypeError as e:
        logger.warning(f"Failed to encode object as JSON for Redis key '{key}': {e}")
        return False