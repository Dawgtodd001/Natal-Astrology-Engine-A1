"""
Dependencies for FastAPI endpoints
"""
from typing import Optional, Dict
import time
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_api_key_from_header

# Dependency for API key with rate limiting
def get_api_key(
    api_key: str = Depends(get_api_key_from_header),
    db: Session = Depends(get_db)
) -> str:
    """
    Get, validate API key and check rate limits
    
    Args:
        api_key: API key from header
        db: Database session
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Update last_used timestamp for this API key
    from app.models import ApiKey
    from datetime import datetime
    
    # Apply rate limiting
    rate_limiter.check_rate_limit(api_key, db)
    
    # Update last_used timestamp (don't block the request if this fails)
    try:
        api_key_db = db.query(ApiKey).filter(ApiKey.key == api_key).first()
        if api_key_db:
            api_key_db.last_used = datetime.utcnow().isoformat()
            db.commit()
    except Exception:
        # Don't let timestamp update failure affect the request
        pass
    
    return api_key


class RateLimiter:
    """
    Dynamic rate limiter using API key limits from database
    
    For production, consider using Redis or a similar distributed store
    """
    def __init__(self):
        # Dictionary to store request timestamps by API key
        self.request_logs: Dict[str, list] = {}
        # Default rate limit settings (used as fallback)
        self.default_rate_limit = 60  # Requests allowed per minute 
        self.default_daily_limit = 1000  # Default daily request limit
        # Time windows in seconds
        self.minute_window = 60
        self.daily_window = 86400  # 24 hours in seconds
        # Cache of API key rate limits to avoid frequent DB lookups
        self.rate_limit_cache: Dict[str, dict] = {}
        self.cache_ttl = 300  # Cache TTL in seconds (5 minutes)
        self.last_cache_refresh: Dict[str, float] = {}
    
    def _get_api_key_limits(self, api_key: str, db: Session) -> dict:
        """
        Get rate limits for an API key from database or cache
        
        Args:
            api_key: API key to check
            db: Database session
            
        Returns:
            Dictionary with rate_limit and last_updated values
        """
        current_time = time.time()
        
        # Check if we have a recent cache entry
        if (api_key in self.rate_limit_cache and 
            current_time - self.last_cache_refresh.get(api_key, 0) < self.cache_ttl):
            return self.rate_limit_cache[api_key]
        
        # Query database for API key settings
        from app.models import ApiKey
        api_key_db = db.query(ApiKey).filter(ApiKey.key == api_key).first()
        
        if not api_key_db:
            # Should not happen since we validate keys before this
            return {"rate_limit": self.default_rate_limit, "daily_limit": self.default_daily_limit}
        
        # Store in cache
        limits = {
            "rate_limit": api_key_db.rate_limit or self.default_rate_limit,
            "daily_limit": api_key_db.daily_limit if hasattr(api_key_db, 'daily_limit') else self.default_daily_limit
        }
        self.rate_limit_cache[api_key] = limits
        self.last_cache_refresh[api_key] = current_time
        
        return limits
    
    def check_rate_limit(self, api_key: str, db: Session):
        """
        Check if rate limit is exceeded for an API key
        
        Args:
            api_key: API key to check
            db: Database session
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        current_time = time.time()
        
        # Get rate limits for this API key
        limits = self._get_api_key_limits(api_key, db)
        minute_limit = limits["rate_limit"]
        daily_limit = limits["daily_limit"]
        
        # Initialize if API key not in logs
        if api_key not in self.request_logs:
            self.request_logs[api_key] = []
        
        # Count requests in time windows
        minute_old = current_time - self.minute_window
        day_old = current_time - self.daily_window
        
        # Filter timestamps within the time windows
        minute_requests = [t for t in self.request_logs[api_key] if t > minute_old]
        daily_requests = [t for t in self.request_logs[api_key] if t > day_old]
        
        # Update the request logs with only those within the daily window
        self.request_logs[api_key] = daily_requests
        
        # Check minute rate limit
        if len(minute_requests) >= minute_limit:
            retry_after = int(min(self.request_logs[api_key]) + self.minute_window - current_time) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please try again after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Check daily rate limit
        if len(daily_requests) >= daily_limit:
            retry_after = int(min(self.request_logs[api_key]) + self.daily_window - current_time) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily rate limit exceeded. Please try again after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Add current timestamp
        self.request_logs[api_key].append(current_time)

# Create a global instance of the rate limiter
rate_limiter = RateLimiter()
