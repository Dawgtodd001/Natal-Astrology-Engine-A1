"""
Rate limiting middleware for the API Gateway.

This middleware implements rate limiting for API requests based on the API key,
client IP address, and endpoint-specific limits.
"""

import time
import logging
import hashlib
from typing import Awaitable, Callable, Dict, Optional, Tuple, Union

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.core.config import settings

logger = logging.getLogger("api_gateway")

# Simple in-memory rate limit store
# In a production environment, this should be replaced with Redis or another
# distributed cache to support horizontal scaling.
# Structure: {key: (count, timestamp)}
RATE_LIMIT_STORE: Dict[str, Tuple[int, float]] = {}

# Rate limit window in seconds (default: 60 seconds)
RATE_LIMIT_WINDOW = 60

# Default rate limits
DEFAULT_RATE_LIMIT = 60  # 60 requests per minute


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that implements rate limiting for API requests.
    """
    
    def __init__(
        self, 
        app, 
        rate_limit_window: int = RATE_LIMIT_WINDOW,
        default_rate_limit: int = DEFAULT_RATE_LIMIT,
        exclude_paths: Optional[list] = None
    ):
        """
        Initialize middleware.
        
        Args:
            app: ASGI application
            rate_limit_window: Time window for rate limiting in seconds
            default_rate_limit: Default rate limit for requests
            exclude_paths: List of path prefixes to exclude from rate limiting
        """
        super().__init__(app)
        self.rate_limit_window = rate_limit_window
        self.default_rate_limit = default_rate_limit
        self.exclude_paths = exclude_paths or [
            "/docs", 
            "/redoc", 
            "/openapi.json", 
            "/metrics", 
            "/health"
        ]
        
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process a request and apply rate limiting.
        
        Args:
            request: Request object
            call_next: Function to call the next middleware/handler
            
        Returns:
            Response from the next middleware/handler or a 429 Too Many Requests response
        """
        # Skip rate limiting for excluded paths
        path = request.url.path
        if self._should_skip_rate_limiting(path):
            return await call_next(request)
            
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Get API key info and rate limit details
        api_key_info = getattr(request.state, "api_key", None)
        
        # Determine appropriate rate limit based on API key, route, etc.
        rate_limit = self._get_rate_limit(request, api_key_info)
        
        # Check rate limit
        if not self._is_rate_limited(client_id, rate_limit):
            # If not rate limited, proceed to next middleware
            return await call_next(request)
        else:
            # If rate limited, return 429 Too Many Requests
            return self._create_rate_limited_response(rate_limit)
            
    def _should_skip_rate_limiting(self, path: str) -> bool:
        """
        Check if a path should be excluded from rate limiting.
        
        Args:
            path: Request path
            
        Returns:
            True if rate limiting should be skipped, False otherwise
        """
        return any(path.startswith(prefix) for prefix in self.exclude_paths)
        
    def _get_client_identifier(self, request: Request) -> str:
        """
        Get a unique identifier for the client.
        
        Uses API key if available, otherwise falls back to IP address.
        
        Args:
            request: Request object
            
        Returns:
            Unique client identifier as a string
        """
        # Try to get the API key from the request state (set by AuthMiddleware)
        api_key_info = getattr(request.state, "api_key", None)
        
        if api_key_info and isinstance(api_key_info, dict):
            # If API key info is available, use the API key ID as the identifier
            return f"api_key:{api_key_info.get('id', 'unknown')}"
        else:
            # Otherwise, use the client IP address
            client_ip = request.client.host if request.client else "unknown"
            
            # Get path for more granular rate limiting
            path = request.url.path
            
            # Create a combined identifier for IP-based rate limiting per path
            return f"ip:{client_ip}:path:{hashlib.md5(path.encode()).hexdigest()[:16]}"
            
    def _get_rate_limit(self, request: Request, api_key_info: Optional[Dict]) -> int:
        """
        Determine the appropriate rate limit for this request.
        
        Order of precedence:
        1. Route-specific rate limit
        2. API key rate limit
        3. Service-specific rate limit
        4. Default rate limit
        
        Args:
            request: Request object
            api_key_info: API key information from AuthMiddleware
            
        Returns:
            Rate limit as requests per minute
        """
        # 1. Check for route-specific rate limit
        # In a real implementation, this would look up the route in the database
        # and get the rate limit setting
        
        # 2. Check for API key rate limit
        if api_key_info and isinstance(api_key_info, dict):
            # Admin keys may have higher rate limits
            if api_key_info.get("is_admin", False):
                return settings.ADMIN_RATE_LIMIT or 1000
                
            # Use API key specific rate limit if available
            api_key_rate_limit = api_key_info.get("rate_limit", 0)
            if api_key_rate_limit > 0:
                return api_key_rate_limit
                
        # 3. Check for service-specific rate limit
        service = self._get_service_from_path(request.url.path)
        if service == "chart":
            return settings.CHART_SERVICE_RATE_LIMIT or 40
        elif service == "interpretation":
            return settings.INTERPRETATION_SERVICE_RATE_LIMIT or 20
            
        # 4. Fall back to default rate limit
        return self.default_rate_limit
        
    def _is_rate_limited(self, client_id: str, rate_limit: int) -> bool:
        """
        Check if a client is rate limited.
        
        Args:
            client_id: Unique client identifier
            rate_limit: Maximum requests per minute
            
        Returns:
            True if client is rate limited, False otherwise
        """
        current_time = time.time()
        
        # Get existing rate limit data
        count, timestamp = RATE_LIMIT_STORE.get(client_id, (0, current_time))
        
        # If the window has expired, reset the counter
        if current_time - timestamp > self.rate_limit_window:
            RATE_LIMIT_STORE[client_id] = (1, current_time)
            return False
            
        # Increment the counter
        new_count = count + 1
        RATE_LIMIT_STORE[client_id] = (new_count, timestamp)
        
        # Check if the client has exceeded the rate limit
        return new_count > rate_limit
        
    def _create_rate_limited_response(self, rate_limit: int) -> Response:
        """
        Create a 429 Too Many Requests response.
        
        Args:
            rate_limit: Current rate limit
            
        Returns:
            Response object
        """
        from starlette.responses import JSONResponse
        
        # Calculate reset time
        reset_seconds = self.rate_limit_window
        
        # Create response with appropriate headers
        response = JSONResponse(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Rate limit exceeded. Maximum {rate_limit} requests per {self.rate_limit_window} seconds."
            }
        )
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Reset"] = str(reset_seconds)
        response.headers["Retry-After"] = str(reset_seconds)
        
        return response
        
    def _get_service_from_path(self, path: str) -> str:
        """
        Extract service name from the path.
        
        Args:
            path: Request path
            
        Returns:
            Service name
        """
        # Extract service from path (e.g., /api/v1/chart/ -> chart)
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "api" and parts[1].startswith("v"):
            return parts[2]
            
        # Default service name
        return "api_gateway"