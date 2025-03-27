"""
Interpretation endpoints for the API Gateway service

This module provides endpoints for chart interpretations.
"""

import logging
import json
from typing import Dict, Any, Optional, List

import httpx
from sqlalchemy.exc import SQLAlchemyError

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND, HTTP_202_ACCEPTED

from api_gateway.app.core.settings import settings
from api_gateway.app.db.session import get_db

# Get logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/natal", summary="Get natal chart interpretation")
async def natal_interpretation(chart_data: Dict[str, Any]) -> JSONResponse:
    """
    Get interpretation for a natal chart
    
    Args:
        chart_data: Chart data for interpretation
    
    Returns:
        JSONResponse: Chart interpretation
    """
    try:
        # Get async_mode from request if provided
        async_mode = chart_data.pop("async_mode", settings.ENABLE_ASYNC_MODE)
        
        # Create service URL
        service_url = f"{settings.SERVICE_INTERPRETATION}/api/v1/interpretations/natal"
        
        # Set timeout to avoid blocking (longer for sync mode)
        timeout = httpx.Timeout(30.0 if not async_mode else 5.0, connect=2.0)
        
        # Add async_mode to request
        chart_data["async_mode"] = async_mode
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.post(service_url, json=chart_data)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to interpretation service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to interpretation service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error in natal interpretation: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error in natal interpretation: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/transit", summary="Get transit chart interpretation")
async def transit_interpretation(transit_data: Dict[str, Any]) -> JSONResponse:
    """
    Get interpretation for a transit chart
    
    Args:
        transit_data: Transit chart data for interpretation
    
    Returns:
        JSONResponse: Transit chart interpretation
    """
    try:
        # Get async_mode from request if provided
        async_mode = transit_data.pop("async_mode", settings.ENABLE_ASYNC_MODE)
        
        # Create service URL
        service_url = f"{settings.SERVICE_INTERPRETATION}/api/v1/interpretations/transit"
        
        # Set timeout to avoid blocking (longer for sync mode)
        timeout = httpx.Timeout(30.0 if not async_mode else 5.0, connect=2.0)
        
        # Add async_mode to request
        transit_data["async_mode"] = async_mode
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.post(service_url, json=transit_data)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to interpretation service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to interpretation service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error in transit interpretation: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error in transit interpretation: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/tasks/{task_id}", summary="Get task status")
async def get_task_status(task_id: str) -> JSONResponse:
    """
    Get status of an asynchronous interpretation task
    
    Args:
        task_id: Task ID from an asynchronous interpretation request
    
    Returns:
        JSONResponse: Task status and result if completed
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_INTERPRETATION}/api/v1/interpretations/tasks/{task_id}"
        
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
        logger.error(f"Error connecting to interpretation service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to interpretation service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error getting task status: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error getting task status: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/templates", summary="Get available interpretation templates")
async def get_templates() -> JSONResponse:
    """
    Get available interpretation templates
    
    Returns:
        JSONResponse: List of available interpretation templates
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_INTERPRETATION}/api/v1/interpretations/templates"
        
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
        logger.error(f"Error connecting to interpretation service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to interpretation service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error getting templates: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error getting templates: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/templates/{template_id}", summary="Get interpretation template")
async def get_template(template_id: str) -> JSONResponse:
    """
    Get specific interpretation template
    
    Args:
        template_id: Template ID
    
    Returns:
        JSONResponse: Interpretation template
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_INTERPRETATION}/api/v1/interpretations/templates/{template_id}"
        
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
        logger.error(f"Error connecting to interpretation service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to interpretation service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error getting template: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error getting template: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )