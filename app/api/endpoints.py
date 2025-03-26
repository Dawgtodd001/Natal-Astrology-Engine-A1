"""
FastAPI endpoints for the Natal Astrology Engine
"""
from typing import Dict, Any, Optional
import datetime
import hashlib
import traceback
import time
import os

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from app.utils.error_handling import handle_exception, ErrorCodes
from app.utils.pagination import paginate_query
from app.api.admin import validate_admin_password

from app.database import get_db
from app.api.schemas import (
    ChartRequest, ChartResponse, ChartInterpretationRequest,
    PaginationParams, PageInfo, PaginatedResponse, ApiKeyResponse,
    ChartCalculationResponse
)
from app.api.dependencies import get_api_key, RateLimiter
from app.core.chart import create_natal_chart
from app.core.houses import get_available_house_systems
from app.core.interpretation import render_interpretation
from app.models import ChartCalculation, ApiKey
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api")

# Rate limiter instance
rate_limiter = RateLimiter()


def log_chart_calculation(
    db: Session,
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone: str,
    house_system: str,
    zodiac_type: str
):
    """
    Log chart calculation to database for analytics and caching
    
    Args:
        db: Database session
        birth_date: Birth date
        birth_time: Birth time
        latitude: Birth latitude
        longitude: Birth longitude
        timezone: Timezone
        house_system: House system used
        zodiac_type: Zodiac system used
    """
    try:
        # Generate cache key for this calculation
        cache_key_input = f"{birth_date}|{birth_time}|{latitude}|{longitude}|{timezone}|{house_system}|{zodiac_type}"
        cache_key = hashlib.sha256(cache_key_input.encode()).hexdigest()
        
        # Check if this cache key already exists
        existing_entry = db.query(ChartCalculation).filter(ChartCalculation.cache_key == cache_key).first()
        
        if existing_entry:
            # Update the timestamp on the existing entry
            existing_entry.calculation_timestamp = datetime.datetime.utcnow().isoformat()
            db.commit()
            logger.info(
                "Updated existing chart calculation log",
                extra={"cache_key": cache_key}
            )
            return
        
        # Create a new log entry if no duplicate found
        calculation = ChartCalculation(
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            house_system=house_system,
            zodiac_type=zodiac_type,
            calculation_timestamp=datetime.datetime.utcnow().isoformat(),
            cache_key=cache_key
        )
        
        db.add(calculation)
        
        try:
            db.commit()
        except Exception as e:
            # Handle potential race condition if another process added the same cache key
            db.rollback()
            
            # Check again for duplicate after rollback
            existing_entry = db.query(ChartCalculation).filter(ChartCalculation.cache_key == cache_key).first()
            if existing_entry:
                existing_entry.calculation_timestamp = datetime.datetime.utcnow().isoformat()
                db.commit()
                logger.info(
                    "Updated existing chart calculation log after conflict",
                    extra={"cache_key": cache_key}
                )
            else:
                # If it's another type of error, raise it
                raise
        
        logger.info(
            "Chart calculation logged",
            extra={
                "birth_date": birth_date,
                "latitude": latitude,
                "longitude": longitude,
                "house_system": house_system,
                "zodiac_type": zodiac_type,
                "cache_key": cache_key
            }
        )
    except Exception as e:
        logger.error(
            f"Failed to log chart calculation: {str(e)}",
            extra={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )


@router.post("/chart", response_model=ChartResponse)
async def generate_chart(
    request: ChartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Generate a natal chart based on birth data
    
    Args:
        request: Chart request data
        background_tasks: FastAPI background tasks
        db: Database session
        api_key: API key for authentication
        
    Returns:
        Complete chart data
    """
    logger.info(
        "Chart generation requested",
        extra={
            "api_key": api_key,
            "birth_date": request.birth_date,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "house_system": request.house_system,
            "zodiac_type": request.zodiac_type
        }
    )
    
    # Apply rate limiting
    rate_limiter.check_rate_limit(api_key, db)
    
    try:
        # Auto-resolve timezone if not provided
        if not request.timezone:
            logger.info("Auto-resolving timezone from coordinates")
            request.auto_resolve_timezone()
            logger.info(f"Resolved timezone: {request.timezone}")
        
        # Generate the chart
        chart_data = create_natal_chart(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone,
            house_system=request.house_system,
            zodiac_type=request.zodiac_type
        )
        
        logger.info(
            "Chart generated successfully",
            extra={
                "planet_count": len(chart_data["planets"]),
                "aspect_count": len(chart_data["aspects"]),
                "house_system": request.house_system
            }
        )
        
        # Log the calculation in the background
        background_tasks.add_task(
            log_chart_calculation,
            db=db,
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone,
            house_system=request.house_system,
            zodiac_type=request.zodiac_type
        )
        
        return chart_data
    
    except ValueError as e:
        # Handle validation errors
        handle_exception(
            e, 
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCodes.INVALID_INPUT,
            message=f"Invalid chart parameters: {str(e)}"
        )
    except Exception as e:
        # Handle other calculation errors
        logger.error(
            f"Chart calculation failed: {str(e)}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "birth_date": request.birth_date,
                "birth_time": request.birth_time,
                "traceback": traceback.format_exc()
            }
        )
        handle_exception(
            e, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCodes.CALCULATION_ERROR,
            message=f"Chart calculation failed: {str(e)}"
        )


@router.post("/interpret", response_class=PlainTextResponse)
async def interpret_chart(
    request: ChartInterpretationRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Generate and return an interpretation of a natal chart
    
    Args:
        request: Chart interpretation request
        db: Database session
        api_key: API key for authentication
        
    Returns:
        Text interpretation of the chart
    """
    logger.info(
        "Chart interpretation requested",
        extra={
            "api_key": api_key,
            "birth_date": request.birth_date,
            "template_name": request.template_name,
            "house_system": request.house_system,
            "zodiac_type": request.zodiac_type
        }
    )
    
    # Apply rate limiting
    rate_limiter.check_rate_limit(api_key, db)
    
    try:
        # Auto-resolve timezone if not provided
        if not request.timezone:
            logger.info("Auto-resolving timezone from coordinates")
            request.auto_resolve_timezone()
            logger.info(f"Resolved timezone: {request.timezone}")
            
        # Generate the chart
        chart_data = create_natal_chart(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone,
            house_system=request.house_system,
            zodiac_type=request.zodiac_type
        )
        
        # Create birth info dictionary for template rendering
        birth_info = {
            "birth_date": request.birth_date,
            "birth_time": request.birth_time,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "timezone": request.timezone
        }
        
        logger.info(
            f"Using template: {request.template_name}",
            extra={
                "template": request.template_name
            }
        )
        
        # Render the interpretation
        interpretation = render_interpretation(
            db=db,
            chart_data=chart_data,
            birth_info=birth_info,
            template_name=request.template_name
        )
        
        logger.info(
            "Interpretation generated successfully",
            extra={
                "text_length": len(interpretation),
                "template_used": request.template_name
            }
        )
        
        return interpretation
    
    except ValueError as e:
        # Handle validation errors
        handle_exception(
            e, 
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCodes.INVALID_INPUT,
            message=f"Invalid chart parameters: {str(e)}"
        )
    except Exception as e:
        # Handle other interpretation errors
        logger.error(
            f"Interpretation failed: {str(e)}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "birth_date": request.birth_date,
                "template": request.template_name,
                "traceback": traceback.format_exc()
            }
        )
        handle_exception(
            e, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCodes.CALCULATION_ERROR,
            message=f"Chart interpretation failed: {str(e)}"
        )


@router.get("/house-systems")
async def get_house_systems(
    api_key: str = Depends(get_api_key)
):
    """
    Get available house systems with descriptions
    
    Args:
        api_key: API key for authentication
        
    Returns:
        Dictionary of house systems and descriptions
    """
    logger.info("House systems requested", extra={"api_key": api_key})
    
    try:
        house_systems = get_available_house_systems()
        logger.info(
            "House systems retrieved successfully",
            extra={"system_count": len(house_systems)}
        )
        return house_systems
    
    except Exception as e:
        logger.error(
            f"Failed to retrieve house systems: {str(e)}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        handle_exception(
            e, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Failed to retrieve house systems"
        )


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    
    Returns status of the API and its dependencies
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with health check results
    """
    start_time = time.time()
    
    # Check database connection
    db_status = "healthy"
    db_error = None
    try:
        # Simple query to test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1")).fetchone()
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)
    
    # Check if we have API keys in the database
    api_keys_status = "healthy"
    api_keys_count = 0
    try:
        from app.models import ApiKey
        api_keys_count = db.query(ApiKey).count()
        if api_keys_count == 0:
            api_keys_status = "warning"
    except Exception as e:
        api_keys_status = "unhealthy"
    
    # Overall status
    status = "healthy"
    if db_status == "unhealthy" or api_keys_status == "unhealthy":
        status = "unhealthy"
    elif api_keys_status == "warning":
        status = "warning"
    
    response_time = time.time() - start_time
    
    return {
        "status": status,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": {
                "status": db_status,
                "error": db_error
            },
            "api_keys": {
                "status": api_keys_status,
                "count": api_keys_count
            }
        },
        "response_time_seconds": round(response_time, 3)
    }


@router.get("/admin/chart-history")
async def get_chart_history(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin_password: str = Query(..., description="Admin password for accessing chart history")
):
    """
    Development endpoint to view chart calculation history
    
    THIS ENDPOINT SHOULD BE DISABLED IN PRODUCTION.
    
    Args:
        pagination: Pagination parameters
        db: Database session
        admin_password: Admin password for authentication
        
    Returns:
        Paginated list of chart calculations
        
    Raises:
        HTTPException: If admin password is invalid
    """
    # Validate admin password
    validate_admin_password(admin_password)
    
    logger.warning("Admin chart history endpoint accessed", extra={"authorized": True})
    
    try:
        # Prepare query
        query = db.query(ChartCalculation).order_by(ChartCalculation.calculation_timestamp.desc())
        
        # Define a function to convert DB model to API schema
        def chart_calculation_to_schema(calc: ChartCalculation) -> ChartCalculationResponse:
            return ChartCalculationResponse(
                id=calc.id,
                birth_date=calc.birth_date,
                birth_time=calc.birth_time,
                latitude=calc.latitude,
                longitude=calc.longitude,
                timezone=calc.timezone,
                house_system=calc.house_system,
                zodiac_type=calc.zodiac_type,
                calculation_timestamp=calc.calculation_timestamp
            )
        
        # Use the pagination utility function
        paginated_response = paginate_query(
            query=query,
            pagination=pagination,
            model_to_schema=chart_calculation_to_schema
        )
        
        # Add information about chart history
        response_dict = paginated_response.model_dump()
        response_dict["description"] = "Chart calculation history for analytics and monitoring"
        
        return response_dict
    
    except Exception as e:
        logger.error(
            f"Failed to retrieve chart history: {str(e)}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        handle_exception(
            e, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCodes.DATABASE_ERROR,
            message="Failed to retrieve chart history"
        )


@router.get("/admin/keys")
async def get_api_keys(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin_password: str = Query(..., description="Admin password for accessing API keys")
):
    """
    Development endpoint to view available API keys
    
    THIS ENDPOINT SHOULD BE DISABLED IN PRODUCTION.
    
    Args:
        pagination: Pagination parameters
        db: Database session
        admin_password: Admin password for authentication
        
    Returns:
        Paginated list of API keys in the system
        
    Raises:
        HTTPException: If admin password is invalid
    """
    # Validate admin password
    validate_admin_password(admin_password)
    
    logger.warning("Admin API key endpoint accessed", extra={"authorized": True})
    
    try:
        # Prepare query
        query = db.query(ApiKey).order_by(ApiKey.id)
        
        # Define a function to convert DB model to API schema
        def api_key_to_schema(key: ApiKey) -> ApiKeyResponse:
            return ApiKeyResponse(
                name=key.name,
                key=key.key,
                enabled=key.enabled,
                rate_limit=key.rate_limit,
                daily_limit=key.daily_limit,
                created_at=key.created_at
            )
        
        # Use the pagination utility function
        paginated_response = paginate_query(
            query=query,
            pagination=pagination,
            model_to_schema=api_key_to_schema
        )
        
        # Add usage instructions
        response_dict = paginated_response.model_dump()
        response_dict["usage_instructions"] = "Use the X-API-Key header with one of these keys to authenticate API requests."
        
        return response_dict
    
    except Exception as e:
        logger.error(
            f"Failed to retrieve API keys: {str(e)}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        handle_exception(
            e, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCodes.DATABASE_ERROR,
            message="Failed to retrieve API keys"
        )
