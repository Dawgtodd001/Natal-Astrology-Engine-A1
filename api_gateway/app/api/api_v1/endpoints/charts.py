"""
Chart calculation endpoints for the API Gateway service

This module provides endpoints for astrological chart calculations.
"""

import logging
import json
from typing import Dict, Any, Optional, List

import httpx
from sqlalchemy.exc import SQLAlchemyError

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND

from api_gateway.app.core.settings import settings
from api_gateway.app.db.session import get_db

# Get logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/natal", summary="Calculate natal chart")
async def calculate_natal_chart(chart_data: Dict[str, Any]) -> JSONResponse:
    """
    Calculate natal chart
    
    Args:
        chart_data: Chart calculation data
    
    Returns:
        JSONResponse: Calculated natal chart
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_CHART_CALCULATION}/api/v1/charts/natal"
        
        # Set timeout to avoid blocking
        timeout = httpx.Timeout(10.0, connect=2.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.post(service_url, json=chart_data)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to chart calculation service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to chart calculation service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error in natal chart calculation: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error in natal chart calculation: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/transit", summary="Calculate transit chart")
async def calculate_transit_chart(transit_data: Dict[str, Any]) -> JSONResponse:
    """
    Calculate transit chart
    
    Args:
        transit_data: Transit chart calculation data
    
    Returns:
        JSONResponse: Calculated transit chart
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_CHART_CALCULATION}/api/v1/charts/transit"
        
        # Set timeout to avoid blocking
        timeout = httpx.Timeout(10.0, connect=2.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Forward request to service
            response = await client.post(service_url, json=transit_data)
            
            # Return response from service
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to chart calculation service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to chart calculation service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error in transit chart calculation: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error in transit chart calculation: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/house-systems", summary="Get available house systems")
async def get_house_systems() -> JSONResponse:
    """
    Get available house systems
    
    Returns:
        JSONResponse: List of available house systems
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_CHART_CALCULATION}/api/v1/charts/house-systems"
        
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
        logger.error(f"Error connecting to chart calculation service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to chart calculation service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error getting house systems: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error getting house systems: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/aspects", summary="Get aspects configuration")
async def get_aspects() -> JSONResponse:
    """
    Get aspects configuration
    
    Returns:
        JSONResponse: Aspects configuration
    """
    try:
        # Create service URL
        service_url = f"{settings.SERVICE_CHART_CALCULATION}/api/v1/charts/aspects"
        
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
        logger.error(f"Error connecting to chart calculation service: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error connecting to chart calculation service: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error getting aspects configuration: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Unexpected error getting aspects configuration: {str(e)}"
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )