"""
Aspect calculations for astrological charts
"""
from typing import List, Dict, Any, Tuple


def calculate_aspects(planets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate aspects between planets in a chart
    
    Args:
        planets: List of planet data dictionaries
        
    Returns:
        List of aspect dictionaries
    """
    aspects = []
    
    # Define major aspects and their orbs
    aspect_types = {
        "conjunction": (0, 8),
        "opposition": (180, 8),
        "trine": (120, 8),
        "square": (90, 8),
        "sextile": (60, 6),
        "quincunx": (150, 5),
        "semisextile": (30, 3),
        "semisquare": (45, 3),
        "sesquisquare": (135, 3),
    }
    
    # Calculate aspects between each pair of planets
    for i, planet1 in enumerate(planets):
        for j, planet2 in enumerate(planets):
            # Skip same planet or if we've already done this pair
            if i >= j:
                continue
                
            # Calculate angular distance between planets
            p1_total_degrees = planet1["degree"] + (planet1["minutes"] / 60)
            p2_total_degrees = planet2["degree"] + (planet2["minutes"] / 60)
            
            # Convert signs to degrees (0-359)
            zodiac_signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                           "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            
            p1_absolute_pos = zodiac_signs.index(planet1["sign"]) * 30 + p1_total_degrees
            p2_absolute_pos = zodiac_signs.index(planet2["sign"]) * 30 + p2_total_degrees
            
            # Calculate smaller angle between planets (0-180)
            angle = abs(p1_absolute_pos - p2_absolute_pos)
            if angle > 180:
                angle = 360 - angle
                
            # Check if angle matches any aspect type
            for aspect_type, (aspect_angle, orb) in aspect_types.items():
                if abs(angle - aspect_angle) <= orb:
                    # Determine if aspect is applying or separating
                    # This is a simplification; real calculation would consider 
                    # planet speeds and directions
                    applying = planet1["speed"] > planet2["speed"]
                    
                    # Add to aspects list
                    aspects.append({
                        "planet1": planet1["name"],
                        "planet2": planet2["name"],
                        "aspect_type": aspect_type,
                        "orb": abs(angle - aspect_angle),
                        "applying": applying
                    })
                    
                    break  # Only one aspect type per planet pair
    
    return aspects


def filter_major_aspects(aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter aspects to only include major ones (conjunction, opposition, trine, square, sextile)
    
    Args:
        aspects: List of all aspects
        
    Returns:
        List of major aspects only
    """
    major_types = ["conjunction", "opposition", "trine", "square", "sextile"]
    return [a for a in aspects if a["aspect_type"] in major_types]
