"""
Logging middleware for the API Gateway service

This middleware enhances request logging with structured information.
"""

import time
import uuid
import logging
import json
from typing import Optional, Dict, Any, Callable

import fastapi
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from api_gateway.app.core.settings import settings
from api_gateway.app.middleware.correlation import get_correlation_id

# Initialize logger
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enhance request logging with structured information
    
    This middleware:
    1. Logs incoming requests with correlation ID, method, path, and client info
    2. Logs outgoing responses with status code and response time
    3. Structured logs for easier analysis
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize middleware
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
        
    async def dispatch(self, request: fastapi.Request, call_next):
        """
        Process request, logging request and response information
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response
        """
        # Get correlation ID from context
        correlation_id = get_correlation_id()
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "correlation_id": correlation_id,
                "request": {
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_host": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("User-Agent", "unknown")
                }
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            logger.info(
                f"Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "response": {
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2)
                    }
                }
            )
            
            # Add X-Response-Time header
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
        except Exception as e:
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "correlation_id": correlation_id,
                    "response": {
                        "status_code": 500,
                        "duration_ms": round(duration_ms, 2),
                        "error": str(e)
                    }
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise