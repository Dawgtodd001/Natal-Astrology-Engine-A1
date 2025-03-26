"""
House system calculations for astrological charts
"""
from typing import Dict, List, Any


def calculate_houses(
    date_time: str, 
    latitude: float, 
    longitude: float, 
    house_system: str = "placidus"
) -> List[Dict[str, Any]]:
    """
    Calculate house cusps using specified house system
    
    Args:
        date_time: Date and time in ISO format
        latitude: Birth latitude
        longitude: Birth longitude
        house_system: House system to use
        
    Returns:
        List of house dictionaries with sign, degree, and minute information
    """
    # In a real implementation, this would do the calculation.
    # For this example, we're letting flatlib handle the house calculation
    # in the chart.py module.
    
    # This is a placeholder for completeness of the module structure
    houses = []
    return houses


def get_available_house_systems() -> Dict[str, str]:
    """
    Get available house systems with descriptions
    
    Returns:
        Dictionary mapping house system keys to descriptions
    """
    house_systems = {
        "placidus": "Most commonly used modern system, based on time division of meridian crossing.",
        "whole_sign": "Ancient system where each sign equals one whole house, starting with rising sign.",
        "equal": "Houses of equal size (30°), with the first house cusp at the Ascendant.",
        "koch": "Time-based system popular in Germany, with house cusps determined by ecliptic points.",
        "regiomontanus": "Medieval system using the celestial equator for time division.",
        "campanus": "Medieval system using the prime vertical for house division.",
        "porphyry": "Simple system that divides the ecliptic between angles into three equal parts.",
        "morinus": "Houses are equally spaced along the celestial equator.",
        "polich_page": "Topocentric system based on the Earth's rotation and proximity to planets.",
        "topocentric": "Similar to Placidus but adjusted for Earth's curvature and observer location.",
        "alcabitius": "Semi-arc system used in traditional astrology."
    }
    
    return house_systems
