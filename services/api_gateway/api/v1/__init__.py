"""
API v1 router for Natal Astrology API Gateway
"""
from fastapi import APIRouter

# Create the main router for API v1
router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint for API v1
    
    Returns:
        dict: Status information
    """
    return {
        "status": "ok",
        "version": "v1",
        "service": "api_gateway"
    }