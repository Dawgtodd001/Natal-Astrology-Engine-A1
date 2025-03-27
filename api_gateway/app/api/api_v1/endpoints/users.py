"""
User profile endpoints for the API Gateway service

This module provides endpoints for user profile management.
"""

import logging
import json
from typing import Dict, Any, Optional, List

import httpx
from sqlalchemy.exc import SQLAlchemyError

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from api_gateway.app.core.settings import settings
from api_gateway.app.db.session import get_db

# Get logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/", summary="Get all user profiles")
async def get_user_profiles() -> JSONResponse:
    """
    Get all user profiles
    
    Returns:
        JSONResponse: List of user profiles
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_USER_PROFILE}/api/v1/users"
        
        # Set timeout to avoid blocking
        timeout = httpx.Timeout(5.0, connect=2.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.get(service_url)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to user profile service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to user profile service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error getting user profiles: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error getting user profiles: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/{user_id}", summary="Get user profile by ID")
async def get_user_profile(user_id: str) -> JSONResponse:
    """
    Get user profile by ID
    
    Args:
        user_id: User ID
        
    Returns:
        JSONResponse: User profile
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_USER_PROFILE}/api/v1/users/{user_id}"
        
        # Set timeout to avoid blocking
        timeout = httpx.Timeout(5.0, connect=2.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.get(service_url)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to user profile service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to user profile service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error getting user profile: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error getting user profile: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/", summary="Create user profile")
async def create_user_profile(user_data: Dict[str, Any]) -> JSONResponse:
    """
    Create user profile
    
    Args:
        user_data: User profile data
        
    Returns:
        JSONResponse: Created user profile
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_USER_PROFILE}/api/v1/users"
        
        # Set timeout to avoid blocking
        timeout = httpx.Timeout(5.0, connect=2.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.post(service_url, json=user_data)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to user profile service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to user profile service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error creating user profile: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error creating user profile: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/{user_id}", summary="Update user profile")
async def update_user_profile(user_id: str, user_data: Dict[str, Any]) -> JSONResponse:
    """
    Update user profile
    
    Args:
        user_id: User ID
        user_data: Updated user profile data
        
    Returns:
        JSONResponse: Updated user profile
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_USER_PROFILE}/api/v1/users/{user_id}"
        
        # Set timeout to avoid blocking
        timeout = httpx.Timeout(5.0, connect=2.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.put(service_url, json=user_data)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to user profile service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to user profile service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error updating user profile: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error updating user profile: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/{user_id}", summary="Delete user profile")
async def delete_user_profile(user_id: str) -> JSONResponse:
    """
    Delete user profile
    
    Args:
        user_id: User ID
        
    Returns:
        JSONResponse: Deletion status
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_USER_PROFILE}/api/v1/users/{user_id}"
        
        # Set timeout to avoid blocking
        timeout = httpx.Timeout(5.0, connect=2.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.delete(service_url)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to user profile service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to user profile service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting user profile: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error deleting user profile: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/{user_id}/charts", summary="Get user's saved charts")
async def get_user_charts(user_id: str) -> JSONResponse:
    """
    Get charts saved for a user
    
    Args:
        user_id: User ID
        
    Returns:
        JSONResponse: List of user's saved charts
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_USER_PROFILE}/api/v1/users/{user_id}/charts"
        
        # Set timeout to avoid blocking
        timeout = httpx.Timeout(5.0, connect=2.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.get(service_url)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to user profile service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to user profile service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error getting user charts: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error getting user charts: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/{user_id}/charts", summary="Save chart for user")
async def save_user_chart(user_id: str, chart_data: Dict[str, Any]) -> JSONResponse:
    """
    Save chart for a user
    
    Args:
        user_id: User ID
        chart_data: Chart data to save
        
    Returns:
        JSONResponse: Saved chart information
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_USER_PROFILE}/api/v1/users/{user_id}/charts"
        
        # Set timeout to avoid blocking
        timeout = httpx.Timeout(5.0, connect=2.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.post(service_url, json=chart_data)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to user profile service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to user profile service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error saving user chart: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error saving user chart: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )