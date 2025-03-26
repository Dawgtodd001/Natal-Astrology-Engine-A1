"""
Error handling utilities for the application
"""
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class ErrorCodes:
    """Error codes for API responses"""
    INVALID_INPUT = "INVALID_INPUT"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

def handle_exception(
    exception: Exception,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: str = ErrorCodes.INTERNAL_ERROR,
    message: Optional[str] = None,
    log_level: int = logging.ERROR,
) -> None:
    """
    Handle exceptions uniformly across the application
    
    Args:
        exception: The exception to handle
        status_code: HTTP status code to return
        error_code: Application-specific error code
        message: Custom message (uses str(exception) if None)
        log_level: Logging level for this error
        
    Raises:
        HTTPException: Formatted exception with consistent structure
    """
    error_message = message or str(exception)
    logger.log(log_level, f"{error_code}: {error_message}", exc_info=exception)
    
    raise HTTPException(
        status_code=status_code,
        detail={
            "error_code": error_code,
            "message": error_message,
            "type": type(exception).__name__
        }
    )