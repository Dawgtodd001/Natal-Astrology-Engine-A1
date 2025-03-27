"""
Rate limiting middleware for the API Gateway service

This middleware implements rate limiting for API requests.
"""

import time
import logging
import json
import asyncio
from typing import Optional, Dict, Any, Callable, Tuple, List

import fastapi
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from api_gateway.app.core.settings import settings
from api_gateway.app.middleware.correlation import get_correlation_id

# Initialize logger
logger = logging.getLogger(__name__)

# In-memory storage for rate limits (will be replaced with Redis in production)
# Format: {ip_or_key: [(timestamp, count), ...]}
RATE_LIMITS: Dict[str, List[Tuple[float, int]]] = {}

# Default rate limit: 60 requests per minute
DEFAULT_LIMIT = settings.RATE_LIMIT_DEFAULT_LIMIT
DEFAULT_WINDOW = settings.RATE_LIMIT_DEFAULT_WINDOW  # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to implement rate limiting for API requests
    
    This middleware:
    1. Identifies clients by API key or IP address
    2. Tracks request counts within time windows
    3. Rejects requests that exceed the rate limit
    4. Adds rate limit headers to responses
    """
    
    def __init__(
        self, 
        app: fastapi.FastAPI,
        limit: int = DEFAULT_LIMIT,
        window: int = DEFAULT_WINDOW,
        api_key_header: str = "X-API-Key",
        limit_by_ip: bool = True
    ):
        """
        Initialize middleware
        
        Args:
            app: FastAPI application
            limit: Maximum number of requests allowed in window
            window: Time window in seconds
            api_key_header: Header name for API key
            limit_by_ip: Whether to limit by IP address or API key
        """
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.api_key_header = api_key_header
        self.limit_by_ip = limit_by_ip
    
    def get_client_id(self, request: fastapi.Request) -> str:
        """
        Get client identifier for rate limiting
        
        Args:
            request: FastAPI request
            
        Returns:
            Client identifier string (API key or IP address)
        """
        # Try to get API key from header
        api_key = request.headers.get(self.api_key_header)
        
        if api_key and not self.limit_by_ip:
            # Use API key as identifier
            return f"key:{api_key}"
        else:
            # Use IP address as identifier
            client_host = request.client.host if request.client else "unknown"
            return f"ip:{client_host}"
    
    def is_rate_limited(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Check if client is rate limited
        
        Args:
            client_id: Client identifier
            
        Returns:
            Tuple of (is_limited, current_requests, remaining_requests)
        """
        # Get current timestamps for client
        now = time.time()
        window_start = now - self.window
        
        # Initialize or clean expired entries
        if client_id not in RATE_LIMITS:
            RATE_LIMITS[client_id] = []
        else:
            # Remove expired timestamps
            RATE_LIMITS[client_id] = [
                (ts, count) for ts, count in RATE_LIMITS[client_id] 
                if ts > window_start
            ]
        
        # Calculate current count in window
        current = sum(count for _, count in RATE_LIMITS[client_id])
        
        # Check if rate limited
        is_limited = current >= self.limit
        remaining = max(0, self.limit - current)
        
        return is_limited, current, remaining
    
    def update_rate_limit(self, client_id: str) -> None:
        """
        Update rate limit counter for client
        
        Args:
            client_id: Client identifier
        """
        now = time.time()
        
        # Add new timestamp
        if client_id in RATE_LIMITS:
            RATE_LIMITS[client_id].append((now, 1))
        else:
            RATE_LIMITS[client_id] = [(now, 1)]
    
    async def dispatch(self, request: fastapi.Request, call_next):
        """
        Process request, applying rate limiting
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response or 429 Too Many Requests
        """
        # Skip rate limiting for certain endpoints
        path = request.url.path
        if path.startswith("/metrics") or path.startswith("/health"):
            return await call_next(request)
        
        # Get client identifier
        client_id = self.get_client_id(request)
        
        # Check rate limit
        is_limited, current, remaining = self.is_rate_limited(client_id)
        
        # If rate limited, return 429
        if is_limited:
            logger.warning(
                f"Rate limit exceeded for client {client_id}",
                extra={
                    "correlation_id": get_correlation_id(),
                    "client_id": client_id,
                    "limit": self.limit,
                    "window": self.window,
                    "current": current
                }
            )
            
            # Use starlette Response to avoid dependency cycle with FastAPI
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too many requests",
                    "message": f"Rate limit of {self.limit} requests per {self.window} seconds exceeded",
                    "retry_after": self.window
                },
                headers={
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + self.window)),
                    "Retry-After": str(self.window)
                }
            )
        
        # Update rate limit
        self.update_rate_limit(client_id)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window))
        
        return response