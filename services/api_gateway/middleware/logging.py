"""
Logging middleware for API requests

This middleware logs details of API requests and responses
"""
import time
import logging
import json
from typing import Callable, Dict, Any

# Try to import FastAPI
try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    
# Configure logging
logger = logging.getLogger(__name__)

# Import correlation ID utilities
from services.api-gateway.middleware.correlation import get_correlation_id


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log API requests and responses
    
    This logs details of each request and response for auditing and debugging
    """
    # Paths that won't be logged to avoid noise
    QUIET_PATHS = [
        "/metrics",
        "/api/health",
    ]
    
    def __init__(self, app: ASGIApp):
        """Initialize the middleware"""
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and log details
        
        Args:
            request: FastAPI/Starlette request
            call_next: Next middleware in the chain
            
        Returns:
            Response with logging added
        """
        # Get correlation ID for this request
        correlation_id = get_correlation_id()
        
        # Start timer
        start_time = time.time()
        
        # Check if this path should be logged
        quiet = self._is_quiet_path(request.url.path)
        
        # Log request details (if not quiet)
        if not quiet:
            await self._log_request(request, correlation_id)
            
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response details (if not quiet)
            if not quiet:
                self._log_response(request, response, duration, correlation_id)
                
            return response
            
        except Exception as e:
            # Log exception
            duration = time.time() - start_time
            self._log_exception(request, e, duration, correlation_id)
            
            # Re-raise exception to be handled by exception handlers
            raise
            
    def _is_quiet_path(self, path: str) -> bool:
        """
        Check if a path should be logged quietly (minimal logging)
        
        Args:
            path: URL path to check
            
        Returns:
            True if the path should be logged quietly, False otherwise
        """
        # Check if path starts with any of the quiet paths
        return any(path.startswith(quiet_path) for quiet_path in self.QUIET_PATHS)
        
    async def _log_request(self, request: Request, correlation_id: str):
        """
        Log details of a request
        
        Args:
            request: FastAPI/Starlette request
            correlation_id: Correlation ID for this request
        """
        # Build log data
        log_data = {
            "correlation_id": correlation_id,
            "type": "request",
            "method": request.method,
            "path": request.url.path,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        # Add query parameters if present
        query_params = dict(request.query_params)
        if query_params:
            log_data["query_params"] = query_params
            
        # Don't log body for security and performance reasons
        
        # Log as JSON if structured logging is enabled
        if hasattr(logger, "json"):
            logger.info("API request", extra=log_data)
        else:
            logger.info(f"API request: {json.dumps(log_data)}")
            
    def _log_response(self, request: Request, response: Response, duration: float, correlation_id: str):
        """
        Log details of a response
        
        Args:
            request: FastAPI/Starlette request
            response: Starlette response
            duration: Request duration in seconds
            correlation_id: Correlation ID for this request
        """
        # Build log data
        log_data = {
            "correlation_id": correlation_id,
            "type": "response",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "content_type": response.headers.get("content-type", ""),
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
            
        # Log as JSON if structured logging is enabled
        if hasattr(logger, "json"):
            logger.log(log_level, "API response", extra=log_data)
        else:
            logger.log(log_level, f"API response: {json.dumps(log_data)}")
            
    def _log_exception(self, request: Request, exception: Exception, duration: float, correlation_id: str):
        """
        Log details of an exception
        
        Args:
            request: FastAPI/Starlette request
            exception: Exception that occurred
            duration: Request duration in seconds
            correlation_id: Correlation ID for this request
        """
        # Build log data
        log_data = {
            "correlation_id": correlation_id,
            "type": "exception",
            "method": request.method,
            "path": request.url.path,
            "error": str(exception),
            "error_type": exception.__class__.__name__,
            "duration_ms": round(duration * 1000, 2),
        }
        
        # Log as JSON if structured logging is enabled
        if hasattr(logger, "json"):
            logger.exception("API exception", extra=log_data)
        else:
            logger.exception(f"API exception: {json.dumps(log_data)}")
            
    def _get_client_ip(self, request: Request) -> str:
        """
        Get the client IP address from a request
        
        Args:
            request: FastAPI/Starlette request
            
        Returns:
            Client IP address
        """
        # Try to get from X-Forwarded-For header (common in proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Get the first IP in the list
            return forwarded_for.split(",")[0].strip()
            
        # Fall back to client.host
        return request.client.host if request.client else ""