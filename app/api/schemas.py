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
    birth_city: Optional[str] = Field(None, description="Birth city name (for display purposes only)")
    
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
        if v is not None:
            from app.core.utils.timezone import normalize_timezone
            normalized = normalize_timezone(v)
            if normalized not in pytz.all_timezones:
                raise ValueError(f"Invalid timezone: {v}")
            return normalized
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


class TransitAspectInfo(BaseModel):
    """
    Transit-to-natal aspect information
    """
    from_planet: str = Field(..., description="Transit planet name")
    to_planet: str = Field(..., description="Natal planet name")
    aspect_type: str = Field(..., description="Aspect type (e.g., 'conjunction', 'opposition')")
    angle: float = Field(..., description="Angle in degrees")
    orb: float = Field(..., description="Orb in degrees")
    applying: bool = Field(..., description="Whether the aspect is applying (getting stronger) or separating")
    is_major: bool = Field(..., description="Whether this is a major aspect")


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
    chart_type: str = Field("natal", description="Type of chart: 'natal' or 'transit'")
    planets: List[PlanetInfo]
    houses: List[HouseInfo]
    aspects: List[AspectInfo]
    angles: Dict[str, AngleInfo]


class TransitResponse(BaseModel):
    """
    Response model for transit chart calculation
    """
    natal_chart: ChartResponse
    transit_chart: ChartResponse
    transit_aspects: List[TransitAspectInfo]
    aspect_grid: Dict[str, Dict[str, Optional[str]]] = Field(
        ..., 
        description="2D grid of transit-to-natal aspects. Keys are transit planets, values are dicts with natal planet keys and aspect type values."
    )


class TransitRequest(BaseModel):
    """
    Request model for transit chart calculation
    """
    birth_date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    birth_time: str = Field(..., description="Birth time in HH:MM format (24-hour)")
    birth_latitude: float = Field(..., description="Birth latitude (-90 to 90)")
    birth_longitude: float = Field(..., description="Birth longitude (-180 to 180)")
    birth_timezone: Optional[str] = Field(None, description="Birth IANA timezone name. If not provided, will be auto-detected.")
    birth_city: Optional[str] = Field(None, description="Birth city name (for display purposes only)")
    
    transit_date: str = Field(..., description="Transit date in YYYY-MM-DD format")
    transit_time: str = Field(..., description="Transit time in HH:MM format (24-hour)")
    transit_latitude: Optional[float] = Field(None, description="Transit latitude (-90 to 90). If not provided, birth latitude is used.")
    transit_longitude: Optional[float] = Field(None, description="Transit longitude (-180 to 180). If not provided, birth longitude is used.")
    transit_timezone: Optional[str] = Field(None, description="Transit IANA timezone name. If not provided, will be auto-detected.")
    transit_city: Optional[str] = Field(None, description="Transit city name (for display purposes only)")
    
    house_system: str = Field("placidus", description="House system to use")
    zodiac_type: str = Field("tropical", description="Zodiac type ('tropical' or 'sidereal')")
    include_minor_aspects: bool = Field(False, description="Whether to include minor aspects")
    orb_tolerance: float = Field(2.0, description="Orb tolerance for aspects (in degrees)", ge=0.0, le=10.0)
    
    # Validators
    @field_validator('birth_date', 'transit_date')
    def validate_date(cls, v, info):
        """Validate date format"""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError(f"{info.field_name} must be in YYYY-MM-DD format")
        return v
    
    @field_validator('birth_time', 'transit_time')
    def validate_time(cls, v, info):
        """Validate time format"""
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f"{info.field_name} must be in HH:MM format (24-hour)")
        return v
    
    @field_validator('birth_latitude', 'transit_latitude')
    def validate_latitude(cls, v, info):
        """Validate latitude range"""
        if v is not None and (v < -90 or v > 90):
            raise ValueError(f"{info.field_name} must be between -90 and 90")
        return v
    
    @field_validator('birth_longitude', 'transit_longitude')
    def validate_longitude(cls, v, info):
        """Validate longitude range"""
        if v is not None and (v < -180 or v > 180):
            raise ValueError(f"{info.field_name} must be between -180 and 180")
        return v
    
    @field_validator('birth_timezone', 'transit_timezone')
    def validate_timezone(cls, v, info):
        """Validate timezone name"""
        if v is not None:
            from app.core.utils.timezone import normalize_timezone
            normalized = normalize_timezone(v)
            if normalized not in pytz.all_timezones:
                raise ValueError(f"Invalid timezone: {v}")
            return normalized
        return v
    
    @model_validator(mode='after')
    def default_transit_values(self):
        """Set default transit values if not provided"""
        # If transit location not provided, use birth location
        if self.transit_latitude is None:
            self.transit_latitude = self.birth_latitude
        
        if self.transit_longitude is None:
            self.transit_longitude = self.birth_longitude
        
        # Auto-resolve timezones if not provided
        if self.birth_timezone is None:
            self.birth_timezone = resolve_timezone(self.birth_latitude, self.birth_longitude)
        
        if self.transit_timezone is None:
            self.transit_timezone = resolve_timezone(self.transit_latitude, self.transit_longitude)
        
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


class ChartInterpretationRequest(ChartRequest):
    """
    Request model for chart interpretation
    Extends ChartRequest with template and AI options
    """
    template_name: str = Field("basic_text", description="Name of interpretation template to use")
    use_ai: bool = Field(False, description="Whether to use AI-powered interpretation")
    ai_style: Optional[str] = Field(None, description="AI interpretation style (concise, detailed, spiritual, psychological)")


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


class UserProfileResponse(BaseModel):
    """
    User profile for stored birth data
    """
    id: int
    name: str
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    timezone: str
    notes: Optional[str] = None
    is_admin: bool
    created_at: str
