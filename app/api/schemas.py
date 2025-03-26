"""
Pydantic schemas for API request and response validation
"""
from typing import List, Dict, Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.generics import GenericModel
import re
import pytz
from app.core.utils.timezone import resolve_timezone

# Generic type for pagination
T = TypeVar('T')


class ChartRequest(BaseModel):
    """
    Request model for chart generation
    """
    birth_date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    birth_time: str = Field(..., description="Birth time in HH:MM format (24-hour)")
    latitude: float = Field(..., description="Birth latitude (-90 to 90)")
    longitude: float = Field(..., description="Birth longitude (-180 to 180)")
    timezone: Optional[str] = Field(None, description="IANA timezone name (e.g., 'America/New_York'). If not provided, will be auto-detected from coordinates.")
    house_system: str = Field("placidus", description="House system to use")
    zodiac_type: str = Field("tropical", description="Zodiac type ('tropical' or 'sidereal')")
    
    # Validators
    @field_validator('birth_date')
    def validate_birth_date(cls, v):
        """Validate birth date format"""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError("birth_date must be in YYYY-MM-DD format")
        return v
    
    @field_validator('birth_time')
    def validate_birth_time(cls, v):
        """Validate birth time format"""
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError("birth_time must be in HH:MM format (24-hour)")
        return v
    
    @field_validator('latitude')
    def validate_latitude(cls, v):
        """Validate latitude range"""
        if v < -90 or v > 90:
            raise ValueError("latitude must be between -90 and 90")
        return v
    
    @field_validator('longitude')
    def validate_longitude(cls, v):
        """Validate longitude range"""
        if v < -180 or v > 180:
            raise ValueError("longitude must be between -180 and 180")
        return v
    
    @field_validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone name"""
        if v is not None and v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v
        
    @model_validator(mode='after')
    def auto_resolve_timezone(self):
        """Auto-resolve timezone if not provided"""
        if self.timezone is None:
            resolved_tz = resolve_timezone(self.latitude, self.longitude)
            self.timezone = resolved_tz
            print(f"Auto-resolved timezone: {resolved_tz} for coordinates {self.latitude}, {self.longitude}")
        return self
    
    @field_validator('house_system')
    def validate_house_system(cls, v):
        """Validate house system name"""
        valid_systems = ["placidus", "whole_sign", "equal", "koch", "regiomontanus", 
                        "campanus", "porphyry", "morinus", "polich_page", "topocentric", 
                        "alcabitius"]
        if v.lower() not in valid_systems:
            raise ValueError(f"Invalid house system: {v}")
        return v.lower()
    
    @field_validator('zodiac_type')
    def validate_zodiac_type(cls, v):
        """Validate zodiac type"""
        valid_types = ["tropical", "sidereal"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid zodiac type: {v}")
        return v.lower()


class PlanetInfo(BaseModel):
    """
    Planet information in chart
    """
    name: str
    sign: str
    degree: int
    minutes: int
    house: int
    retrograde: bool
    speed: float


class HouseInfo(BaseModel):
    """
    House information in chart
    """
    number: int
    sign: str
    degree: int
    minutes: int


class AspectInfo(BaseModel):
    """
    Aspect information in chart
    """
    planet1: str
    planet2: str
    aspect_type: str
    orb: float
    applying: bool


class AngleInfo(BaseModel):
    """
    Chart angle information
    """
    sign: str
    degree: int
    minutes: int


class AnglesInfo(BaseModel):
    """
    All chart angles
    """
    ascendant: AngleInfo
    midheaven: AngleInfo
    descendant: AngleInfo
    imum_coeli: AngleInfo


class ChartResponse(BaseModel):
    """
    Complete chart data response
    """
    planets: List[PlanetInfo]
    houses: List[HouseInfo]
    aspects: List[AspectInfo]
    angles: Dict[str, AngleInfo]


class ChartInterpretationRequest(ChartRequest):
    """
    Request model for chart interpretation
    Extends ChartRequest with template options
    """
    template_name: str = Field("basic_text", description="Name of interpretation template to use")


class PaginationParams(BaseModel):
    """
    Parameters for paginated requests
    """
    page: int = Field(1, description="Page number (1-indexed)", ge=1)
    page_size: int = Field(10, description="Number of items per page", ge=1, le=100)


class PageInfo(BaseModel):
    """
    Pagination metadata
    """
    current_page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(GenericModel, Generic[T]):
    """
    Generic paginated response
    """
    items: List[T]
    page_info: PageInfo


class ApiKeyResponse(BaseModel):
    """
    API key information for admin responses
    """
    name: str
    key: str
    enabled: bool
    rate_limit: int
    daily_limit: int
    created_at: Optional[str]
    
    
class ChartCalculationResponse(BaseModel):
    """
    Chart calculation record for admin responses
    """
    id: int
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    timezone: str
    house_system: str
    zodiac_type: str
    calculation_timestamp: str
