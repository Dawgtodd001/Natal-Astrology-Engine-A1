"""
Authentication middleware for API requests

This middleware checks API keys and handles authentication for protected endpoints
"""
import os
import logging
import time
from typing import Optional, List, Dict, Any, Callable, Tuple, Union

# Try to import FastAPI
try:
    from fastapi import Request, Response, HTTPException
    from fastapi import Security
    from fastapi.security import APIKeyHeader
    from sqlalchemy.orm import Session
    
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    
# Import settings
from shared.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

# Define constants
AUTH_HEADER_NAME = settings.API_KEY_HEADER


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle authentication for API requests
    
    This checks API keys for protected endpoints and validates permissions
    """
    # Paths that don't require authentication
    PUBLIC_PATHS = [
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/health",
        "/metrics",
    ]
    
    def __init__(self, app):
        """Initialize the middleware"""
        super().__init__(app)
        self._api_keys_cache = {}
        self._api_keys_cache_time = 0
        self._cache_ttl = 60  # 1 minute cache TTL
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and handle authentication
        
        Args:
            request: FastAPI/Starlette request
            call_next: Next middleware in the chain
            
        Returns:
            Response if authenticated, 401/403 error otherwise
        """
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
            
        # Get API key from header
        api_key = request.headers.get(AUTH_HEADER_NAME)
        
        # If no API key provided, check if test key is allowed
        if not api_key and self._allow_test_key():
            # Use default test key if no key provided and in development
            api_key = "test_key_1234567890"
            logger.debug("No API key provided, using test key")
            
        # If still no API key, reject the request
        if not api_key:
            logger.warning(f"Authentication failed: No API key provided for {request.url.path}")
            return self._create_error_response(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )
            
        # Validate API key
        is_valid, permissions = await self._validate_api_key(api_key)
        
        if not is_valid:
            logger.warning(f"Authentication failed: Invalid API key for {request.url.path}")
            return self._create_error_response(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
            
        # Check permissions for this endpoint (not implemented yet, future enhancement)
        has_permission = await self._check_permissions(request, permissions)
        
        if not has_permission:
            logger.warning(f"Authorization failed: Insufficient permissions for {request.url.path}")
            return self._create_error_response(
                status_code=HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
            
        # If authenticated and authorized, proceed
        return await call_next(request)
        
    def _is_public_path(self, path: str) -> bool:
        """
        Check if a path is public and doesn't require authentication
        
        Args:
            path: URL path to check
            
        Returns:
            True if the path is public, False otherwise
        """
        # Check if path starts with any of the public paths
        return any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS)
        
    def _allow_test_key(self) -> bool:
        """
        Check if test key is allowed (only in development)
        
        Returns:
            True if test key is allowed, False otherwise
        """
        # Only allow test key in development environment
        return settings.APP_ENV.lower() == "development"
        
    async def _validate_api_key(self, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate an API key
        
        Args:
            api_key: API key to validate
            
        Returns:
            Tuple of (is_valid, permissions)
            - is_valid: True if the API key is valid, False otherwise
            - permissions: Dict of permissions for this API key
        """
        # Check cache first
        now = time.time()
        if api_key in self._api_keys_cache and (now - self._api_keys_cache_time) < self._cache_ttl:
            return True, self._api_keys_cache[api_key]
            
        # For development test key
        if self._allow_test_key() and api_key == "test_key_1234567890":
            # Give admin permissions to test key
            permissions = {"admin": True, "routes": ["*"]}
            self._api_keys_cache[api_key] = permissions
            self._api_keys_cache_time = now
            return True, permissions
            
        # In a production system, we would check the API key in the database
        # This is a placeholder for future implementation
        
        # For now, just allow the hard-coded test key and any key in the environment
        env_key = os.environ.get("DEFAULT_API_KEY")
        if env_key and api_key == env_key:
            permissions = {"admin": True, "routes": ["*"]}
            self._api_keys_cache[api_key] = permissions
            self._api_keys_cache_time = now
            return True, permissions
            
        # If we get here, the API key is invalid
        return False, {}
        
    async def _check_permissions(self, request: Request, permissions: Dict[str, Any]) -> bool:
        """
        Check if the API key has permission for this endpoint
        
        Args:
            request: FastAPI/Starlette request
            permissions: Dict of permissions for this API key
            
        Returns:
            True if the API key has permission, False otherwise
        """
        # Admin keys have access to everything
        if permissions.get("admin", False):
            return True
            
        # In a production system, we would check specific route permissions
        # For now, just return True if the API key is valid
        return True
        
    def _create_error_response(self, status_code: int, detail: str) -> Response:
        """
        Create an error response
        
        Args:
            status_code: HTTP status code
            detail: Error detail message
            
        Returns:
            JSON response with error details
        """
        # Try to import JSONResponse directly rather than from response var
        try:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status_code,
                content={"detail": detail},
                headers={"WWW-Authenticate": f"API key must be provided in {AUTH_HEADER_NAME} header"}
            )
        except ImportError:
            # Fallback if JSONResponse is not available
            from starlette.responses import Response
            import json
            return Response(
                json.dumps({"detail": detail}),
                status_code=status_code,
                media_type="application/json",
                headers={"WWW-Authenticate": f"API key must be provided in {AUTH_HEADER_NAME} header"}
            )