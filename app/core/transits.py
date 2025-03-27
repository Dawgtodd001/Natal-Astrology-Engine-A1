"""
Transit calculations and aspect grid functionality
"""
from typing import Dict, List, Any, Optional, Tuple
import math
from .chart import create_natal_chart


def calculate_transit_chart(
    birth_date: str,
    birth_time: str,
    birth_latitude: float,
    birth_longitude: float,
    birth_timezone: str,
    transit_date: str,
    transit_time: str,
    transit_latitude: float,
    transit_longitude: float,
    transit_timezone: str,
    house_system: str = "placidus",
    zodiac_type: str = "tropical",
    include_minor_aspects: bool = False,
    orb_tolerance: float = 2.0,
) -> Dict[str, Any]:
    """
    Calculate both natal and transit charts and transit-to-natal aspects
    
    Args:
        birth_date: Birth date in YYYY-MM-DD format
        birth_time: Birth time in HH:MM format (24-hour)
        birth_latitude: Birth latitude
        birth_longitude: Birth longitude
        birth_timezone: Birth IANA timezone name
        transit_date: Transit date in YYYY-MM-DD format
        transit_time: Transit time in HH:MM format (24-hour)
        transit_latitude: Transit latitude
        transit_longitude: Transit longitude
        transit_timezone: Transit IANA timezone name
        house_system: House system to use
        zodiac_type: Zodiac type ('tropical' or 'sidereal')
        include_minor_aspects: Whether to include minor aspects like semisextile, quincunx, etc.
        orb_tolerance: Maximum orb (in degrees) to consider for aspects
        
    Returns:
        Dictionary with natal chart, transit chart, transit aspects, and aspect grid
    """
    # Calculate natal chart
    natal_chart = create_natal_chart(
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=birth_latitude,
        longitude=birth_longitude,
        timezone=birth_timezone,
        house_system=house_system,
        zodiac_type=zodiac_type
    )
    natal_chart["chart_type"] = "natal"
    
    # Calculate transit chart
    transit_chart = create_natal_chart(
        birth_date=transit_date,
        birth_time=transit_time,
        latitude=transit_latitude,
        longitude=transit_longitude,
        timezone=transit_timezone,
        house_system=house_system,
        zodiac_type=zodiac_type
    )
    transit_chart["chart_type"] = "transit"
    
    # Calculate transit-to-natal aspects with additional parameters from request
    transit_aspects = calculate_transit_aspects(
        natal_chart, 
        transit_chart,
        include_minor_aspects=include_minor_aspects,
        orb_tolerance=orb_tolerance
    )
    
    # Generate aspect grid
    aspect_grid = generate_aspect_grid(transit_aspects)
    
    return {
        "natal_chart": natal_chart,
        "transit_chart": transit_chart,
        "transit_aspects": transit_aspects,
        "aspect_grid": aspect_grid
    }


def calculate_transit_aspects(
    natal_chart: Dict[str, Any],
    transit_chart: Dict[str, Any],
    include_minor_aspects: bool = False,
    orb_tolerance: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Calculate aspects between transit and natal planets
    
    Args:
        natal_chart: Natal chart data dictionary
        transit_chart: Transit chart data dictionary
        include_minor_aspects: Whether to include minor aspects
        orb_tolerance: Orb tolerance in degrees
        
    Returns:
        List of transit-to-natal aspect dictionaries
    """
    transit_aspects = []
    
    # Define major and minor aspects
    major_aspects = {
        "conjunction": 0,
        "opposition": 180,
        "trine": 120,
        "square": 90,
        "sextile": 60
    }
    
    minor_aspects = {
        "semisextile": 30,
        "semisquare": 45,
        "quintile": 72,
        "sesquiquadrate": 135,
        "quincunx": 150,
        "biquintile": 144
    }
    
    aspects_to_check = major_aspects.copy()
    if include_minor_aspects:
        aspects_to_check.update(minor_aspects)
    
    # Get planet positions from both charts
    natal_planets = natal_chart["planets"]
    transit_planets = transit_chart["planets"]
    
    # For each transit planet, calculate aspects to natal planets
    for transit_planet in transit_planets:
        transit_name = transit_planet["name"]
        transit_position = _calculate_absolute_position(
            transit_planet["sign"],
            transit_planet["degree"],
            transit_planet["minutes"]
        )
        
        for natal_planet in natal_planets:
            natal_name = natal_planet["name"]
            natal_position = _calculate_absolute_position(
                natal_planet["sign"],
                natal_planet["degree"],
                natal_planet["minutes"]
            )
            
            # Calculate angle between planets
            angle_diff = _calculate_angle_difference(transit_position, natal_position)
            
            # Check for aspects
            for aspect_name, aspect_angle in aspects_to_check.items():
                orb = abs(angle_diff - aspect_angle)
                if orb > 180:
                    orb = 360 - orb
                
                if orb <= orb_tolerance:
                    # Determine if aspect is applying (getting stronger) or separating
                    applying = _is_aspect_applying(
                        transit_planet,
                        natal_planet,
                        aspect_angle,
                        angle_diff
                    )
                    
                    transit_aspects.append({
                        "from_planet": transit_name,
                        "to_planet": natal_name,
                        "aspect_type": aspect_name,
                        "angle": aspect_angle,
                        "orb": round(orb, 2),
                        "applying": applying,
                        "is_major": aspect_name in major_aspects
                    })
    
    return transit_aspects


def generate_aspect_grid(transit_aspects: List[Dict[str, Any]]) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Generate a 2D grid of transit-to-natal aspects
    
    Args:
        transit_aspects: List of transit-to-natal aspect dictionaries
        
    Returns:
        2D grid as nested dictionaries with transit planets as outer keys
        and natal planets as inner keys
    """
    # Define standard planet order
    transit_planets = [
        "Sun", "Moon", "Mercury", "Venus", "Mars", 
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"
    ]
    
    natal_planets = [
        "Sun", "Moon", "Mercury", "Venus", "Mars", 
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", 
        "ASC", "MC"
    ]
    
    # Initialize empty grid
    grid = {}
    for t_planet in transit_planets:
        grid[t_planet] = {}
        for n_planet in natal_planets:
            grid[t_planet][n_planet] = None
    
    # Fill grid with aspects
    for aspect in transit_aspects:
        from_planet = aspect["from_planet"]
        to_planet = aspect["to_planet"]
        aspect_type = aspect["aspect_type"]
        
        if from_planet in grid and to_planet in grid[from_planet]:
            grid[from_planet][to_planet] = aspect_type
    
    return grid


def _calculate_absolute_position(sign: str, degree: int, minute: int) -> float:
    """
    Calculate absolute zodiac position in degrees (0-360)
    
    Args:
        sign: Zodiac sign
        degree: Degrees in sign
        minute: Minutes in degree
        
    Returns:
        Absolute position in degrees
    """
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    sign_index = signs.index(sign)
    sign_start = sign_index * 30
    position = sign_start + degree + (minute / 60)
    
    return position


def _calculate_angle_difference(pos1: float, pos2: float) -> float:
    """
    Calculate smallest angle between two zodiac positions
    
    Args:
        pos1: First position in degrees
        pos2: Second position in degrees
        
    Returns:
        Angle difference in degrees (0-180)
    """
    diff = abs(pos1 - pos2) % 360
    if diff > 180:
        diff = 360 - diff
    
    return diff


def _is_aspect_applying(
    transit_planet: Dict[str, Any],
    natal_planet: Dict[str, Any],
    aspect_angle: float,
    current_angle: float
) -> bool:
    """
    Determine if an aspect is applying (getting stronger) or separating
    
    Args:
        transit_planet: Transit planet data
        natal_planet: Natal planet data
        aspect_angle: The target aspect angle
        current_angle: Current angle between planets
        
    Returns:
        True if aspect is applying, False if separating
    """
    # Transit planets move relative to natal planets
    # If transit planet is retrograde, the behavior is reversed
    retrograde = transit_planet.get("retrograde", False)
    
    # Calculate whether moving towards or away from aspect
    towards_aspect = abs(current_angle - aspect_angle) < abs((current_angle + 0.1) - aspect_angle)
    
    # If retrograde, the logic is inverted
    if retrograde:
        towards_aspect = not towards_aspect
    
    return towards_aspect