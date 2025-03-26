"""
Timezone resolution utilities
"""
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime


def resolve_timezone(latitude: float, longitude: float) -> str:
    """
    Resolve timezone from geographic coordinates
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        IANA timezone name (e.g., 'America/New_York')
    """
    # Initialize timezone finder
    tf = TimezoneFinder()
    
    # Get timezone name
    timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
    
    # If timezone not found, use UTC
    if not timezone_str:
        return "UTC"
        
    return timezone_str


def get_utc_offset(timezone_str: str, date_time: datetime = None) -> str:
    """
    Get UTC offset for a timezone at a specific date/time
    
    Args:
        timezone_str: IANA timezone name
        date_time: Datetime object (or current time if None)
        
    Returns:
        UTC offset as a string (e.g., '+05:00')
    """
    if date_time is None:
        date_time = datetime.now()
        
    timezone = pytz.timezone(timezone_str)
    offset = timezone.utcoffset(date_time)
    
    # Convert to hours and minutes
    total_seconds = int(offset.total_seconds())
    hours, remainder = divmod(abs(total_seconds), 3600)
    minutes = remainder // 60
    
    # Format offset string
    sign = "+" if total_seconds >= 0 else "-"
    return f"{sign}{hours:02d}:{minutes:02d}"
