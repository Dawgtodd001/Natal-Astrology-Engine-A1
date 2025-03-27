"""
Correlation ID middleware

This middleware adds a correlation ID to each request for tracking purposes.
It either uses an existing correlation ID from the request headers or generates a new one.
"""

import logging
import uuid
import contextvars
from typing import Optional, Dict, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

# Get logger
logger = logging.getLogger(__name__)

# Create context variable for correlation ID
correlation_id_var = contextvars.ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    """
    Get the current correlation ID from the context
    
    Returns:
        str: Correlation ID
    """
    correlation_id = correlation_id_var.get()
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
    return correlation_id


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to each request
    """
    
    def __init__(self, app: ASGIApp, correlation_id_header: str = "X-Correlation-ID"):
        """
        Initialize the middleware
        
        Args:
            app: ASGI application
            correlation_id_header: Header name for correlation ID
        """
        super().__init__(app)
        self.correlation_id_header = correlation_id_header
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add correlation ID
        
        Args:
            request: FastAPI request
            call_next: Next middleware in the chain
            
        Returns:
            Response: FastAPI response
        """
        # Get correlation ID from request or generate a new one
        correlation_id = request.headers.get(self.correlation_id_header, str(uuid.uuid4()))
        
        # Set correlation ID in context
        correlation_id_var.set(correlation_id)
        
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers[self.correlation_id_header] = correlation_id
        
        return response