"""
Prometheus metrics middleware for FastAPI

This middleware tracks request counts, durations, and status codes
"""
import time
import logging
from typing import Callable, Dict, Any

# Try to import Prometheus and FastAPI
try:
    from prometheus_client import Counter, Histogram
    from starlette.middleware.base import BaseHTTPMiddleware
    from fastapi import Request, Response
    from starlette.types import ASGIApp
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    
# Configure logging
logger = logging.getLogger(__name__)

# Import metrics tracking from shared module
from shared.monitoring.metrics import track_request


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request metrics with Prometheus
    
    This adds metrics for request count, duration, and status codes
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize the middleware"""
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and track metrics
        
        Args:
            request: FastAPI/Starlette request
            call_next: Next middleware in the chain
            
        Returns:
            Response with metrics tracked
        """
        # Skip tracking for metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
            
        # Start timer
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get sanitized path (remove IDs, etc. to prevent cardinality explosion)
        path = sanitize_path(request.url.path)
        
        try:
            # Track metrics using the shared function
            track_request(
                method=request.method,
                endpoint=path,
                status=response.status_code,
                duration=duration
            )
            
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"Error tracking metrics: {str(e)}")
            
        return response


def sanitize_path(path: str) -> str:
    """
    Sanitize a URL path to prevent high cardinality in metrics
    
    Args:
        path: URL path to sanitize
        
    Returns:
        Sanitized path with IDs and other high-cardinality parts removed
    """
    # Split path into parts
    parts = path.split("/")
    
    # Sanitize each part
    for i, part in enumerate(parts):
        # Skip empty parts
        if not part:
            continue
            
        # Replace numeric IDs with {id}
        if part.isdigit():
            parts[i] = "{id}"
            
        # Replace UUID-like parts with {id}
        elif len(part) > 8 and "-" in part:
            parts[i] = "{id}"
            
    # Rejoin path
    sanitized = "/".join(parts)
    
    # Handle trailing slash consistently
    if path.endswith("/") and not sanitized.endswith("/"):
        sanitized += "/"
        
    return sanitized