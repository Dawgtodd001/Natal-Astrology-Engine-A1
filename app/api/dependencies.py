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

# Simplified dependency for API key
def get_api_key(
    api_key: str = Depends(get_api_key_from_header)
) -> str:
    """
    Get and validate API key
    
    Args:
        api_key: API key from header
        
    Returns:
        Validated API key
    """
    return api_key


class RateLimiter:
    """
    Simple in-memory rate limiter
    
    For production, consider using Redis or a similar distributed store
    """
    def __init__(self):
        # Dictionary to store request timestamps by API key
        self.request_logs: Dict[str, list] = {}
        # Requests allowed per minute
        self.rate_limit = 60
        # Time window in seconds
        self.time_window = 60
    
    def check_rate_limit(self, api_key: str):
        """
        Check if rate limit is exceeded for an API key
        
        Args:
            api_key: API key to check
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        current_time = time.time()
        
        # Initialize if API key not in logs
        if api_key not in self.request_logs:
            self.request_logs[api_key] = []
        
        # Remove old timestamps
        self.request_logs[api_key] = [
            t for t in self.request_logs[api_key]
            if current_time - t < self.time_window
        ]
        
        # Check if rate limit exceeded
        if len(self.request_logs[api_key]) >= self.rate_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add current timestamp
        self.request_logs[api_key].append(current_time)
