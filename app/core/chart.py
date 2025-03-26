"""
Core functionality for natal chart calculations
"""
from typing import Dict, List, Any, Optional
import datetime
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

from app.core.aspects import calculate_aspects
from app.core.houses import get_house_system_code, calculate_houses


def create_natal_chart(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone: Optional[str],
    house_system: str = "placidus",
    zodiac_type: str = "tropical"
) -> Dict[str, Any]:
    """
    Generate a complete natal chart based on birth information
    
    Args:
        birth_date: Birth date in YYYY-MM-DD format
        birth_time: Birth time in HH:MM format (24-hour)
        latitude: Birth latitude
        longitude: Birth longitude
        timezone: IANA timezone name
        house_system: House system to use
        zodiac_type: Zodiac type ('tropical' or 'sidereal')
        
    Returns:
        Complete chart data dictionary
        
    Raises:
        ValueError: If timezone is not provided and cannot be resolved
    """
    # Ensure we have a timezone
    if timezone is None:
        from app.core.utils.timezone import resolve_timezone
        timezone = resolve_timezone(latitude, longitude)
        if timezone is None:
            raise ValueError("Timezone could not be resolved from coordinates and was not provided")
    
    # Create Date object in flatlib format
    # Convert ISO format date (YYYY-MM-DD) to flatlib format (YYYY/MM/DD)
    flatlib_date = birth_date.replace('-', '/')
    
    # Convert IANA timezone to UTC offset that flatlib understands
    from app.core.utils.timezone import get_utc_offset
    utc_offset = get_utc_offset(timezone)
    
    # Create the datetime with the correct format
    date = Datetime(flatlib_date, birth_time, utc_offset)
    
    # Create GeoPos object
    pos = GeoPos(latitude, longitude)
    
    # Get the appropriate house system code from our helper function
    hsys = get_house_system_code(house_system)
    
    # Add logging for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Using house system: {house_system}, code: {hsys}")
    
    # Create the chart with the proper house system code
    try:
        # Flatlib directly accepts the house system as a single letter in the hsys parameter
        # We don't need to use constants, we just pass the letter as a string
        logger.info(f"Using flatlib house system code directly: {hsys}")
        
        chart = Chart(date, pos, hsys=hsys, IDs=const.LIST_OBJECTS)
    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        logger.error(f"Date: {date}, Pos: {pos}, hsys: {hsys}, IDs: {const.LIST_OBJECTS}")
        raise
    
    # Extract planetary positions
    planets = []
    for planet_id in const.LIST_PLANETS + [const.NORTH_NODE]:
        obj = chart.getObject(planet_id)
        planets.append({
            "name": obj.id,
            "sign": obj.sign,
            "degree": int(obj.lon) % 30,
            "minutes": int((obj.lon % 30 - int(obj.lon) % 30) * 60),
            "house": int(obj.house),
            "retrograde": obj.retrograde,
            "speed": obj.lonspeed
        })
    
    # Extract house positions
    houses = []
    for i in range(1, 13):
        house = chart.getHouse(i)
        houses.append({
            "number": i,
            "sign": house.sign,
            "degree": int(house.lon) % 30,
            "minutes": int((house.lon % 30 - int(house.lon) % 30) * 60)
        })
    
    # Calculate aspects
    aspects = calculate_aspects(planets)
    
    # Extract angles
    angles = {
        "ascendant": {
            "sign": chart.get(const.ASC).sign,
            "degree": int(chart.get(const.ASC).lon) % 30,
            "minutes": int((chart.get(const.ASC).lon % 30 - int(chart.get(const.ASC).lon) % 30) * 60)
        },
        "midheaven": {
            "sign": chart.get(const.MC).sign,
            "degree": int(chart.get(const.MC).lon) % 30,
            "minutes": int((chart.get(const.MC).lon % 30 - int(chart.get(const.MC).lon) % 30) * 60)
        },
        "descendant": {
            "sign": chart.get(const.DESC).sign,
            "degree": int(chart.get(const.DESC).lon) % 30,
            "minutes": int((chart.get(const.DESC).lon % 30 - int(chart.get(const.DESC).lon) % 30) * 60)
        },
        "imum_coeli": {
            "sign": chart.get(const.IC).sign,
            "degree": int(chart.get(const.IC).lon) % 30,
            "minutes": int((chart.get(const.IC).lon % 30 - int(chart.get(const.IC).lon) % 30) * 60)
        }
    }
    
    # Return complete chart data
    return {
        "planets": planets,
        "houses": houses,
        "aspects": aspects,
        "angles": angles
    }


def get_planet_by_name(planets: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    """
    Find planet data by name
    
    Args:
        planets: List of planet data dictionaries
        name: Planet name to find
        
    Returns:
        Planet data dictionary or None if not found
    """
    for planet in planets:
        if planet["name"].lower() == name.lower():
            return planet
    return None
