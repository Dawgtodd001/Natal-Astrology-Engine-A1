"""
Logging middleware for the API Gateway.

This middleware logs requests and responses with detailed information
for debugging and monitoring purposes.
"""

import time
import logging
import json
from typing import Awaitable, Callable, Dict, List, Optional, Union

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message

logger = logging.getLogger("api_gateway")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs requests and responses with detailed information.
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        sensitive_headers: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None
    ) -> None:
        """
        Initialize the middleware.
        
        Args:
            app: ASGI application
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            sensitive_headers: List of headers to mask in logs
            exclude_paths: List of path prefixes to exclude from logging
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.sensitive_headers = sensitive_headers or [
            "authorization", "cookie", "set-cookie", "x-api-key"
        ]
        self.exclude_paths = exclude_paths or ["/static/", "/docs", "/redoc", "/openapi.json"]
        
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process a request and log request/response details.
        
        Args:
            request: Request object
            call_next: Function to call the next middleware/handler
            
        Returns:
            Response from the next middleware/handler
        """
        # Skip logging for excluded paths
        if self._should_skip_logging(request.url.path):
            return await call_next(request)
            
        # Get correlation ID if available (from CorrelationIdMiddleware)
        correlation_id = getattr(request.state, "correlation_id", None)
        request_id = correlation_id or "unknown"
        
        # Start request timestamp
        start_time = time.time()
        
        # Prepare request logging
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._mask_sensitive_headers(dict(request.headers)),
            "client": {
                "ip": request.client.host if request.client else "unknown",
                "port": request.client.port if request.client else 0,
            },
        }
        
        # Log request body if enabled and available
        if self.log_request_body:
            try:
                # Store original request body
                body = await request.body()
                
                # Log request body (assuming it's JSON)
                try:
                    if body:
                        # Try to parse as JSON
                        request_info["body"] = json.loads(body.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # If not JSON, log as string or base64 if not text
                    try:
                        request_info["body"] = body.decode()
                    except UnicodeDecodeError:
                        import base64
                        request_info["body"] = f"<binary data, base64 encoded: {base64.b64encode(body).decode()}>"
                
                # Re-create body stream for downstream consumers
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
            except Exception as e:
                logger.warning(f"Failed to log request body: {str(e)}")
                
        # Log request
        logger.info(f"API Gateway request received", extra={"request": request_info})
        
        # Process request
        try:
            # Call next middleware
            response = await call_next(request)
            
            # Calculate response time
            duration_ms = (time.time() - start_time) * 1000
            
            # Prepare response logging
            response_info = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "headers": self._mask_sensitive_headers(dict(response.headers)),
            }
            
            # Log response body if enabled
            if self.log_response_body and not self._is_streaming_response(response):
                try:
                    # Get response body
                    original_body = response.body
                    response_info["body"] = self._format_response_body(original_body)
                except Exception as e:
                    logger.warning(f"Failed to log response body: {str(e)}")
                    
            # Log response
            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            logger.log(log_level, f"API Gateway response sent", extra={"response": response_info})
            
            return response
        except Exception as exc:
            # Calculate response time for error case
            duration_ms = (time.time() - start_time) * 1000
            
            # Log exception
            logger.exception(
                f"API Gateway request failed", 
                extra={
                    "request": request_info,
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "duration_ms": round(duration_ms, 2),
                    },
                }
            )
            raise
            
    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Mask sensitive header values for logging.
        
        Args:
            headers: Dictionary of headers
            
        Returns:
            Dictionary with sensitive headers masked
        """
        masked_headers = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                masked_headers[key] = "******"
            else:
                masked_headers[key] = value
        return masked_headers
        
    def _should_skip_logging(self, path: str) -> bool:
        """
        Check if a path should be excluded from logging.
        
        Args:
            path: Request path
            
        Returns:
            True if path should be excluded, False otherwise
        """
        return any(path.startswith(prefix) for prefix in self.exclude_paths)
        
    def _is_streaming_response(self, response: Response) -> bool:
        """
        Check if a response is streaming.
        
        Args:
            response: Response to check
            
        Returns:
            True if response is streaming, False otherwise
        """
        # Check if the response content is streamed
        return (
            response.status_code == 206 or  # Partial content
            "content-encoding" in [h.lower() for h in response.headers] or  # Compressed
            "transfer-encoding" in [h.lower() for h in response.headers] or  # Chunked
            not hasattr(response, "body")  # No body attribute
        )
        
    def _format_response_body(self, body: bytes) -> Union[Dict, List, str]:
        """
        Format response body for logging.
        
        Args:
            body: Response body bytes
            
        Returns:
            Formatted body as JSON object, list, or string
        """
        if not body:
            return ""
            
        try:
            # Try to parse as JSON
            return json.loads(body.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If not JSON, try to decode as string
            try:
                return body.decode()
            except UnicodeDecodeError:
                # If can't decode as string, return base64
                import base64
                return f"<binary data, base64 encoded: {base64.b64encode(body).decode()}>"