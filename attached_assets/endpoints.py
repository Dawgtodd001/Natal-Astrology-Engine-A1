"""
FastAPI endpoints for the Natal Astrology Engine
"""
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
import datetime

from app.database import get_db
from app.api.schemas import ChartRequest, ChartResponse, ChartInterpretationRequest
from app.api.dependencies import get_api_key, RateLimiter
from app.core.chart import create_natal_chart
from app.core.houses import get_available_house_systems
from app.core.interpretation import render_interpretation
from app.models import ChartCalculation

router = APIRouter()

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
    # Create a new log entry
    calculation = ChartCalculation(
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        house_system=house_system,
        zodiac_type=zodiac_type,
        calculation_timestamp=datetime.datetime.utcnow().isoformat()
    )
    
    db.add(calculation)
    db.commit()


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
    # Apply rate limiting
    rate_limiter.check_rate_limit(api_key)
    
    try:
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
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Chart calculation error: {str(e)}")


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
    # Apply rate limiting
    rate_limiter.check_rate_limit(api_key)
    
    try:
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
        
        # Render the interpretation
        interpretation = render_interpretation(
            db=db,
            chart_data=chart_data,
            birth_info=birth_info,
            template_name=request.template_name
        )
        
        return interpretation
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Interpretation error: {str(e)}")


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
    return get_available_house_systems()
