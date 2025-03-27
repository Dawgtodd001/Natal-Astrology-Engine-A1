"""
Correlation ID middleware for request tracing

This middleware adds a correlation ID to each request to track it through the system
"""
import uuid
import logging
import contextvars
from typing import Callable, Dict, Any

# Try to import FastAPI dependencies
try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp, Receive, Scope, Send
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    
# Configure logging
logger = logging.getLogger(__name__)

# Create a context variable to track correlation IDs across async boundaries
correlation_id = contextvars.ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    """
    Get the current correlation ID from context
    
    Returns:
        Current correlation ID or empty string if not set
    """
    return correlation_id.get() or ""


def set_correlation_id(value: str) -> None:
    """
    Set the correlation ID in the current context
    
    Args:
        value: Correlation ID to set
    """
    correlation_id.set(value)


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID
    
    Returns:
        New UUID string
    """
    return str(uuid.uuid4())


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a correlation ID to each request and response
    
    This allows for request tracing across multiple services and components
    """
    HEADER_NAME = "X-Correlation-ID"
    
    def __init__(self, app: ASGIApp):
        """Initialize the middleware"""
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request, adding a correlation ID
        
        Args:
            request: FastAPI/Starlette request
            call_next: Next middleware in the chain
            
        Returns:
            Response with correlation ID header added
        """
        # Try to get correlation ID from the request header
        request_id = request.headers.get(self.HEADER_NAME)
        
        # If no correlation ID in header, generate a new one
        if not request_id:
            request_id = generate_correlation_id()
            
        # Set correlation ID in context for this request
        token = correlation_id.set(request_id)
        
        try:
            # Process the request with correlation ID in context
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers[self.HEADER_NAME] = request_id
            
            return response
            
        finally:
            # Reset the correlation ID context
            correlation_id.reset(token)