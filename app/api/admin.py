"""
Admin utilities for protected endpoints
"""
import os
from fastapi import HTTPException, status
from app.utils.logging import get_logger

logger = get_logger(__name__)

def validate_admin_password(admin_password: str) -> None:
    """
    Validate the admin password for protected admin endpoints
    
    Args:
        admin_password: Password provided in the request
        
    Raises:
        HTTPException: If admin password is invalid or endpoint is disabled in production
    """
    # Get admin password from environment variable
    admin_password_env = os.environ.get("ADMIN_PASSWORD")
    
    # If admin password isn't set in environment, disable endpoint in production
    if not admin_password_env and os.environ.get("ENVIRONMENT") == "production":
        logger.warning("Admin endpoint accessed in production without password set")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin endpoints are disabled in production"
        )
    
    # Use default password only in development when env var is not set
    expected_password = admin_password_env or "natal_admin_2025"
    
    # Check password
    if admin_password != expected_password:
        logger.warning("Unauthorized admin access attempt", extra={"password_length": len(admin_password)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password"
        )