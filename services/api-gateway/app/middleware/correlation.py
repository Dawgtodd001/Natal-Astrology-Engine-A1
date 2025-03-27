"""
Correlation ID middleware for API Gateway.

This middleware ensures each request has a unique correlation ID to track
requests across microservices.
"""

import logging
import uuid
from typing import Awaitable, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("api_gateway")

# Header names
X_CORRELATION_ID = "X-Correlation-ID"
X_REQUEST_ID = "X-Request-ID"  # Alternative header some systems use


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures each request has a correlation ID.
    
    If a correlation ID is provided in the request headers, it is used.
    Otherwise, a new correlation ID is generated.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        header_name: str = X_CORRELATION_ID,
        validate_uuid: bool = True
    ) -> None:
        """
        Initialize the middleware.
        
        Args:
            app: ASGI application
            header_name: Name of the header to use for correlation ID
            validate_uuid: Whether to validate UUIDs provided in headers
        """
        super().__init__(app)
        self.header_name = header_name
        self.validate_uuid = validate_uuid
        
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process a request and add correlation ID.
        
        Args:
            request: Request object
            call_next: Function to call the next middleware/handler
            
        Returns:
            Response from the next middleware/handler
        """
        # Try to get correlation ID from headers (either primary or alternative header)
        correlation_id = self._get_correlation_id_from_headers(request.headers)
        
        # If no correlation ID or validation failed, generate a new one
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        
        # Call the next middleware with our request
        response = await call_next(request)
        
        # Add the correlation ID to the response headers
        response.headers[self.header_name] = correlation_id
        
        return response
        
    def _get_correlation_id_from_headers(self, headers) -> Optional[str]:
        """
        Get correlation ID from request headers.
        
        Args:
            headers: Request headers
            
        Returns:
            Correlation ID if found and valid, None otherwise
        """
        # Check for the primary header first
        correlation_id = headers.get(self.header_name)
        
        # If not found, try the alternative header
        if not correlation_id:
            correlation_id = headers.get(X_REQUEST_ID)
            
        # If not found in either header, return None
        if not correlation_id:
            return None
            
        # Validate UUID if required
        if self.validate_uuid:
            try:
                uuid.UUID(correlation_id)
            except ValueError:
                logger.warning(
                    f"Invalid correlation ID format: {correlation_id}. Using a new ID instead."
                )
                return None
                
        return correlation_id