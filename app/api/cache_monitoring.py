"""
Redis cache monitoring and management endpoints
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.admin import validate_admin_password
from app.utils.redis_cache import (
    get_redis_client, 
    is_redis_available, 
    flush_cache,
    REDIS_URL
)

# Create router
router = APIRouter()

# Set up logger
logger = logging.getLogger(__name__)


class CacheStats(BaseModel):
    """Cache statistics response model"""
    available: bool
    url: str
    keys_count: int
    memory_used: str
    hit_rate: Optional[float] = None
    uptime: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None


class CacheKeyInfo(BaseModel):
    """Cache key information response model"""
    key: str
    type: str
    ttl: int
    size: int
    sample: Optional[str] = None


@router.get("/health", response_model=Dict[str, bool])
async def cache_health():
    """
    Check Redis cache health status
    
    Returns:
        Status indicating if Redis is available
    """
    available = is_redis_available()
    return {"available": available}


@router.get("/stats", response_model=CacheStats)
async def cache_stats(admin_password: str):
    """
    Get Redis cache statistics
    
    Args:
        admin_password: Admin password for authentication
        
    Returns:
        Cache statistics
    """
    # Validate admin password
    validate_admin_password(admin_password)
    
    # Get Redis client
    client = get_redis_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis cache is not available"
        )
    
    try:
        # Get Redis info
        info = client.info()
        
        # Calculate memory usage
        used_memory = int(info.get("used_memory", 0))
        memory_used = f"{used_memory / 1024 / 1024:.2f} MB"
        
        # Calculate hit rate if available
        hits = int(info.get("keyspace_hits", 0))
        misses = int(info.get("keyspace_misses", 0))
        hit_rate = (hits / (hits + misses)) * 100 if (hits + misses) > 0 else 0
        
        # Get uptime
        uptime_seconds = int(info.get("uptime_in_seconds", 0))
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{days}d {hours}h {minutes}m {seconds}s"
        
        # Get key count for astrology related keys
        keys_count = len(client.keys("astro_chart:*"))
        
        return CacheStats(
            available=True,
            url=REDIS_URL.split("@")[-1],  # Don't include credentials
            keys_count=keys_count,
            memory_used=memory_used,
            hit_rate=hit_rate,
            uptime=uptime,
            stats={
                "connected_clients": info.get("connected_clients", 0),
                "evicted_keys": info.get("evicted_keys", 0),
                "expired_keys": info.get("expired_keys", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
        )
    except Exception as e:
        logger.error(f"Error getting Redis stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving Redis statistics: {str(e)}"
        )


@router.get("/keys", response_model=List[CacheKeyInfo])
async def cache_keys(
    admin_password: str,
    pattern: str = "astro_chart:*",
    limit: int = 20
):
    """
    Get Redis cache keys matching a pattern
    
    Args:
        admin_password: Admin password for authentication
        pattern: Key pattern to match (default: astro_chart:*)
        limit: Maximum number of keys to return (default: 20)
        
    Returns:
        List of cache key information
    """
    # Validate admin password
    validate_admin_password(admin_password)
    
    # Get Redis client
    client = get_redis_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis cache is not available"
        )
    
    try:
        # Get keys matching pattern with limit
        keys = client.keys(pattern)[:limit]
        
        result = []
        for key in keys:
            if isinstance(key, bytes):
                key = key.decode("utf-8")
                
            # Get key type
            key_type = client.type(key).decode("utf-8")
            
            # Get TTL
            ttl = client.ttl(key)
            
            # Get size
            if key_type == "string":
                size = len(client.get(key) or b"")
                
                # Get sample of value (first 50 chars)
                try:
                    value = client.get(key)
                    if value and len(value) > 0:
                        sample_value = value.decode("utf-8")[:50] + "..." if len(value) > 50 else value.decode("utf-8")
                    else:
                        sample_value = None
                except:
                    sample_value = None
            else:
                size = 0
                sample_value = None
            
            result.append(CacheKeyInfo(
                key=key,
                type=key_type,
                ttl=ttl,
                size=size,
                sample=sample_value
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error getting Redis keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving Redis keys: {str(e)}"
        )


@router.delete("/flush", response_model=Dict[str, bool])
async def flush_all_cache(admin_password: str):
    """
    Flush all Redis cache data
    
    Args:
        admin_password: Admin password for authentication
        
    Returns:
        Success status
    """
    # Validate admin password
    validate_admin_password(admin_password)
    
    # Flush cache
    success = flush_cache()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to flush Redis cache"
        )
    
    return {"success": True}