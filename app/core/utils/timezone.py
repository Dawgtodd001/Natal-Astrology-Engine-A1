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


def normalize_timezone(timezone_str: str) -> str:
    """
    Convert common timezone names to IANA standard names
    
    Args:
        timezone_str: Common timezone name or abbreviation
        
    Returns:
        IANA timezone name or the original if no match found
    """
    # Dictionary of common timezone names/abbreviations to IANA names
    common_timezones = {
        # US timezones
        "eastern standard": "America/New_York",
        "eastern": "America/New_York",
        "est": "America/New_York",
        "central standard": "America/Chicago",
        "central": "America/Chicago",
        "cst": "America/Chicago",
        "mountain standard": "America/Denver",
        "mountain": "America/Denver",
        "mst": "America/Denver",
        "pacific standard": "America/Los_Angeles",
        "pacific": "America/Los_Angeles",
        "pst": "America/Los_Angeles",
        "alaska standard": "America/Anchorage",
        "alaska": "America/Anchorage",
        "hawaii standard": "Pacific/Honolulu",
        "hawaii": "Pacific/Honolulu",
        
        # European timezones
        "gmt": "Europe/London",
        "bst": "Europe/London",
        "cet": "Europe/Paris",
        "central european": "Europe/Paris",
        "eet": "Europe/Helsinki",
        "eastern european": "Europe/Helsinki",
        
        # Other major timezones
        "jst": "Asia/Tokyo",
        "japan standard": "Asia/Tokyo",
        "aest": "Australia/Sydney",
        "australian eastern": "Australia/Sydney",
        "ist": "Asia/Kolkata",
        "india standard": "Asia/Kolkata"
    }
    
    # Check if the input is a direct match for an IANA timezone
    if timezone_str in pytz.all_timezones:
        return timezone_str
    
    # Try to match against common timezone names
    lowercase_input = timezone_str.lower().strip()
    if lowercase_input in common_timezones:
        return common_timezones[lowercase_input]
    
    # If no match found, return the original string
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
    
    # Try to normalize the timezone first
    timezone_str = normalize_timezone(timezone_str)
    
    try:
        timezone = pytz.timezone(timezone_str)
        offset = timezone.utcoffset(date_time)
        
        # Convert to hours and minutes
        total_seconds = int(offset.total_seconds())
        hours, remainder = divmod(abs(total_seconds), 3600)
        minutes = remainder // 60
        
        # Format offset string
        sign = "+" if total_seconds >= 0 else "-"
        return f"{sign}{hours:02d}:{minutes:02d}"
    except pytz.exceptions.UnknownTimeZoneError:
        # If the timezone name is invalid, return a default
        return "+00:00"
