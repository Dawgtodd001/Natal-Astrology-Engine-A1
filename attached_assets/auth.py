"""
Authentication functionality for the API
"""
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.models import ApiKey
from app.database import get_db

# Define API key header
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(key: str, db: Session) -> bool:
    """
    Verify if an API key is valid
    
    Args:
        key: API key to verify
        db: Database session
        
    Returns:
        True if key is valid, False otherwise
    """
    # Query for the key
    api_key = db.query(ApiKey).filter(
        ApiKey.key == key,
        ApiKey.enabled == True
    ).first()
    
    return api_key is not None


def get_api_key_from_header(
    api_key: str = Security(api_key_header),
    db: Session = Security(get_db)
) -> str:
    """
    Validate API key from header and return it if valid
    
    Args:
        api_key: API key from header
        db: Database session
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not verify_api_key(api_key, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key"
        )
    
    return api_key
