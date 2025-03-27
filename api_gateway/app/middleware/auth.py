"""
Authentication middleware for the API Gateway service

This module provides authentication via API keys.
"""

import logging
from typing import Optional, List, Dict, Any, Callable, Union
from datetime import datetime

import fastapi
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from starlette.middleware.base import BaseHTleware
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from api_gateway.app.db.session import get_db
from api_gateway.app.models.api_key import APIKey as APIKeyModel

# Create API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Get logger
logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTleware):
    """
    Middleware that validates API keys for routes that require authentication
    """
    
    async def dispatch(self, request, call_next):
        # Skip authentication for public endpoints
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/api/v1/health"):
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            logger.warning(f"Unauthorized request to {path} - no API key provided")
            return fastapi.responses.JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "API key is required"
                }
            )
        
        # Get database session
        db = next(get_db())
        
        # Validate API key
        db_api_key = db.query(APIKeyModel).filter(APIKeyModel.key == api_key).first()
        
        if not db_api_key:
            logger.warning(f"Unauthorized request to {path} - invalid API key")
            return fastapi.responses.JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "Invalid API key"
                }
            )
        
        # Check if API key is active
        if not db_api_key.is_active:
            logger.warning(f"Forbidden request to {path} - inactive API key")
            return fastapi.responses.JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "message": "API key is inactive"
                }
            )
        
        # Check if API key has expired
        if db_api_key.expires_at and db_api_key.expires_at < datetime.utcnow():
            logger.warning(f"Forbidden request to {path} - expired API key")
            return fastapi.responses.JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "message": "API key has expired"
                }
            )
        
        # Update API key last used timestamp
        db_api_key.last_used_at = datetime.utcnow()
        db.add(db_api_key)
        db.commit()
        
        # Add API key info to request state
        request.state.api_key = api_key
        request.state.api_key_id = db_api_key.id
        request.state.user_id = db_api_key.user_id
        
        # Continue processing the request
        return await call_next(request)


async def get_api_key(
    api_key_header: str = Security(API_KEY_HEADER),
    db: Session = Depends(get_db)
) -> str:
    """
    Dependency for FastAPI routes to get API key
    
    Args:
        api_key_header: API key from request header
        db: Database session
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If API key is invalid, inactive, or expired
    """
    if not api_key_header:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    # Validate API key
    db_api_key = db.query(APIKeyModel).filter(APIKeyModel.key == api_key_header).first()
    
    if not db_api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check if API key is active
    if not db_api_key.is_active:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="API key is inactive"
        )
    
    # Check if API key has expired
    if db_api_key.expires_at and db_api_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="API key has expired"
        )
    
    # Update API key last used timestamp
    db_api_key.last_used_at = datetime.utcnow()
    db.add(db_api_key)
    db.commit()
    
    return api_key_header