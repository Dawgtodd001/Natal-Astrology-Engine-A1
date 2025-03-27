"""
Prometheus metrics middleware for the API Gateway.

This middleware collects metrics for each request and exports them in Prometheus format.
"""

import time
import logging
from typing import Awaitable, Callable

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from starlette.types import ASGIApp

logger = logging.getLogger("api_gateway")

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    "api_gateway_request_total",
    "Total count of requests by method and path",
    ["method", "endpoint", "service"]
)

REQUEST_TIME = Histogram(
    "api_gateway_request_duration_seconds",
    "Request duration in seconds by method and path",
    ["method", "endpoint", "service"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf"))
)

REQUESTS_IN_PROGRESS = Gauge(
    "api_gateway_requests_in_progress",
    "Gauge of requests currently being processed by method and path",
    ["method", "endpoint", "service"]
)

RESPONSE_STATUS = Counter(
    "api_gateway_response_status",
    "Count of responses by status code, method and path",
    ["method", "endpoint", "status", "service"]
)

ERROR_COUNT = Counter(
    "api_gateway_error_count",
    "Count of errors by method, path and error type",
    ["method", "endpoint", "error_type", "service"]
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware that collects Prometheus metrics for each request.
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        group_paths: bool = True,
        filter_unhandled_paths: bool = True
    ) -> None:
        """
        Initialize the middleware.
        
        Args:
            app: ASGI application
            group_paths: Whether to group similar paths (e.g., /users/123 -> /users/{id})
            filter_unhandled_paths: Whether to filter out unhandled paths (static files, etc.)
        """
        super().__init__(app)
        self.group_paths = group_paths
        self.filter_unhandled_paths = filter_unhandled_paths
        
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process a request and collect metrics.
        
        Args:
            request: Request object
            call_next: Function to call the next middleware/handler
            
        Returns:
            Response from the next middleware/handler
        """
        # Get request details
        method = request.method
        path = self._get_path(request)
        service = self._get_service(request, path)
        
        # Skip metrics for certain paths
        if self.filter_unhandled_paths and self._should_skip_path(path):
            return await call_next(request)
        
        # Track request in progress
        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path, service=service).inc()
        
        # Start timer
        start_time = time.time()
        
        # Process request and handle exceptions
        try:
            response = await call_next(request)
            
            # Record response status
            status_code = response.status_code
            RESPONSE_STATUS.labels(
                method=method, endpoint=path, status=status_code, service=service
            ).inc()
            
            # If error status code, record error
            if 400 <= status_code < 600:
                error_type = "client_error" if status_code < 500 else "server_error"
                ERROR_COUNT.labels(
                    method=method, endpoint=path, error_type=error_type, service=service
                ).inc()
                
            return response
            
        except Exception as exc:
            # Record exception error
            ERROR_COUNT.labels(
                method=method, endpoint=path, error_type=type(exc).__name__, service=service
            ).inc()
            raise
            
        finally:
            # Calculate request duration and record metrics
            duration = time.time() - start_time
            REQUEST_TIME.labels(method=method, endpoint=path, service=service).observe(duration)
            REQUEST_COUNT.labels(method=method, endpoint=path, service=service).inc()
            
            # Request is no longer in progress
            REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path, service=service).dec()
            
    def _get_path(self, request: Request) -> str:
        """
        Get the path for the request, optionally grouping similar paths.
        
        Args:
            request: Request object
            
        Returns:
            Path string, possibly grouped if group_paths is True
        """
        path = request.url.path
        
        # Group paths if enabled (e.g., /users/123 -> /users/{id})
        if self.group_paths:
            try:
                # Extract route from request
                if hasattr(request, "route") and request.route:
                    # Use FastAPI route path
                    return request.route.path
                else:
                    # Fallback to raw path
                    return path
            except Exception:
                # If something goes wrong, use raw path
                return path
        
        return path
        
    def _get_service(self, request: Request, path: str) -> str:
        """
        Get the service name for the request.
        
        Args:
            request: Request object
            path: Request path
            
        Returns:
            Service name
        """
        # Try to get service from request state (set by routing)
        if hasattr(request.state, "service") and request.state.service:
            return request.state.service
            
        # Fallback: Extract service from path (e.g., /api/v1/chart/ -> chart)
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "api" and parts[1].startswith("v"):
            return parts[2]
            
        # Default service name
        return "api_gateway"
        
    def _should_skip_path(self, path: str) -> bool:
        """
        Determine if metrics collection should be skipped for this path.
        
        Args:
            path: Request path
            
        Returns:
            True if metrics should be skipped for this path
        """
        # Skip static files, metrics endpoint itself, etc.
        skip_prefixes = ["/static/", "/favicon.ico", "/metrics"]
        return any(path.startswith(prefix) for prefix in skip_prefixes)