"""
Authentication middleware for the API Gateway.

This middleware validates API keys and enforces access control.
"""

import time
import logging
import secrets
from typing import Awaitable, Callable, Optional, Union, Dict

from fastapi import Request, Response
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from app.core.config import settings
from app.db.session import get_db
from app.models.api_key import ApiKey

logger = logging.getLogger("api_gateway")

# Define the API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Path prefixes that don't require authentication
PUBLIC_PATH_PREFIXES = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
    "/health",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates API keys and enforces access control.
    """
    
    def __init__(self, app, public_paths=None):
        """
        Initialize middleware.
        
        Args:
            app: ASGI application
            public_paths: List of path prefixes that don't require authentication
        """
        super().__init__(app)
        self.public_paths = public_paths or PUBLIC_PATH_PREFIXES
        
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process a request and validate API key.
        
        Args:
            request: Request object
            call_next: Function to call the next middleware/handler
            
        Returns:
            Response from the next middleware/handler
        """
        # Skip authentication for public paths
        path = request.url.path
        if self._is_public_path(path):
            return await call_next(request)
            
        # Look for API key in header
        api_key_value = self._get_api_key_from_request(request)
        if not api_key_value:
            return self._create_unauthorized_response("API key is missing")
            
        # Get DB session
        try:
            # Note: This is a synchronous operation in an async context,
            # which is not ideal for performance. In a real-world application,
            # you might want to use an async DB session or a cache.
            db = next(get_db())
            
            # Validate the API key
            api_key_info = self._validate_api_key(db, api_key_value)
            if not api_key_info:
                return self._create_unauthorized_response("Invalid API key")
            
            # Store API key info in request state for later use
            request.state.api_key = api_key_info
            
            # Update the last_used timestamp in the background
            self._update_api_key_last_used(db, api_key_info["id"])
            
            # Check if the API key is allowed to access the requested service
            service = self._get_service_from_path(path)
            if not self._can_access_service(api_key_info, service):
                return self._create_forbidden_response(
                    f"API key is not authorized to access the {service} service"
                )
                
            # Call the next middleware/handler
            return await call_next(request)
        except Exception as e:
            logger.exception(f"Authentication error: {str(e)}")
            return self._create_unauthorized_response("Authentication failed")
            
    def _is_public_path(self, path: str) -> bool:
        """
        Check if a path is public and doesn't require authentication.
        
        Args:
            path: Request path
            
        Returns:
            True if the path is public, False otherwise
        """
        return any(path.startswith(prefix) for prefix in self.public_paths)
        
    def _get_api_key_from_request(self, request: Request) -> Optional[str]:
        """
        Get API key from the request headers.
        
        Args:
            request: Request object
            
        Returns:
            API key string or None if not found
        """
        # Check API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
            
        # Check query parameter (less secure, but some clients might use it)
        api_key = request.query_params.get("api_key")
        return api_key
        
    def _validate_api_key(self, db: Session, api_key_value: str) -> Optional[Dict]:
        """
        Validate an API key against the database.
        
        Args:
            db: Database session
            api_key_value: API key to validate
            
        Returns:
            Dictionary with API key information if valid, None otherwise
        """
        # Query the database for the API key
        api_key = db.query(ApiKey).filter(
            ApiKey.key == api_key_value,
            ApiKey.enabled == True
        ).first()
        
        # Return None if key not found or disabled
        if not api_key:
            return None
            
        # Convert API key model to dictionary
        return api_key.to_dict()
        
    def _update_api_key_last_used(self, db: Session, api_key_id: int) -> None:
        """
        Update the last_used timestamp for an API key.
        
        Args:
            db: Database session
            api_key_id: ID of the API key to update
        """
        # This could be improved to use a background task
        try:
            api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
            if api_key:
                api_key.last_used = time.time()
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update API key last_used timestamp: {str(e)}")
            db.rollback()
            
    def _get_service_from_path(self, path: str) -> str:
        """
        Extract service name from the path.
        
        Args:
            path: Request path
            
        Returns:
            Service name
        """
        # Extract service from path (e.g., /api/v1/chart/ -> chart)
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "api" and parts[1].startswith("v"):
            return parts[2]
            
        # Default service name
        return "api_gateway"
        
    def _can_access_service(self, api_key_info: Dict, service: str) -> bool:
        """
        Check if the API key can access the requested service.
        
        Args:
            api_key_info: API key information
            service: Service name
            
        Returns:
            True if access is allowed, False otherwise
        """
        # Admin keys can access any service
        if api_key_info.get("is_admin", False):
            return True
            
        # Check specific service permissions
        if service == "chart":
            return api_key_info.get("can_access_chart_service", False)
        elif service == "interpretation":
            return api_key_info.get("can_access_interpretation_service", False)
        elif service == "user_profile":
            return api_key_info.get("can_access_user_profile_service", False)
        
        # For other services, default to allowing access
        return True
        
    def _create_unauthorized_response(self, detail: str) -> Response:
        """
        Create a 401 Unauthorized response.
        
        Args:
            detail: Error detail
            
        Returns:
            Response object
        """
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=HTTP_401_UNAUTHORIZED,
            content={"detail": detail}
        )
        
    def _create_forbidden_response(self, detail: str) -> Response:
        """
        Create a 403 Forbidden response.
        
        Args:
            detail: Error detail
            
        Returns:
            Response object
        """
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=HTTP_403_FORBIDDEN,
            content={"detail": detail}
        )