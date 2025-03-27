"""
Prometheus metrics middleware

This middleware collects metrics about requests and responses for Prometheus.
"""

import time
import logging
from typing import Callable, Dict, Any

import prometheus_client
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from starlette.types import ASGIApp

# Get logger
logger = logging.getLogger(__name__)

# Create metrics
REQUEST_COUNT = prometheus_client.Counter(
    "api_gateway_http_requests_total",
    "Total count of HTTP requests by method and path",
    ["method", "path", "status"]
)

REQUEST_LATENCY = prometheus_client.Histogram(
    "api_gateway_http_request_duration_seconds",
    "HTTP request latency in seconds by method and path",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0, float("inf"))
)

ERROR_COUNT = prometheus_client.Counter(
    "api_gateway_error_total",
    "Total count of errors by error type",
    ["error_type"]
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics about requests and responses
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and collect metrics
        
        Args:
            request: FastAPI request
            call_next: Next middleware in the chain
            
        Returns:
            Response: FastAPI response
        """
        # Get request path and method
        path = request.url.path
        method = request.method
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate request latency
            duration = time.time() - start_time
            
            # Record metrics
            REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
            REQUEST_COUNT.labels(method=method, path=path, status=response.status_code).inc()
            
            return response
        except Exception as e:
            # Record error metric
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            
            # Re-raise exception
            raise