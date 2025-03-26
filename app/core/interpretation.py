"""
Chart interpretation functionality
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import jinja2
import os

from app.models import PlanetInterpretation, HouseInterpretation, AspectInterpretation, InterpretationTemplate
from app.core.chart import get_planet_by_name
from app.core.aspects import filter_major_aspects


def get_planet_sign_interpretation(db: Session, planet: str, sign: str) -> Optional[str]:
    """
    Get interpretation for a planet in a sign
    
    Args:
        db: Database session
        planet: Planet name
        sign: Zodiac sign name
        
    Returns:
        Interpretation text or None if not found
    """
    interpretation = db.query(PlanetInterpretation).filter(
        PlanetInterpretation.planet == planet,
        PlanetInterpretation.sign == sign
    ).first()
    
    if interpretation:
        return interpretation.interpretation
    
    return f"No interpretation available for {planet} in {sign}."


def get_planet_house_interpretation(db: Session, planet: str, house: int) -> Optional[str]:
    """
    Get interpretation for a planet in a house
    
    Args:
        db: Database session
        planet: Planet name
        house: House number (1-12)
        
    Returns:
        Interpretation text or None if not found
    """
    interpretation = db.query(HouseInterpretation).filter(
        HouseInterpretation.planet == planet,
        HouseInterpretation.house == house
    ).first()
    
    if interpretation:
        return interpretation.interpretation
    
    return f"No interpretation available for {planet} in house {house}."


def get_aspect_interpretation(db: Session, planet1: str, planet2: str, aspect_type: str) -> Optional[str]:
    """
    Get interpretation for an aspect between planets
    
    Args:
        db: Database session
        planet1: First planet name
        planet2: Second planet name
        aspect_type: Type of aspect
        
    Returns:
        Interpretation text or None if not found
    """
    # Try exact match
    interpretation = db.query(AspectInterpretation).filter(
        AspectInterpretation.planet1 == planet1,
        AspectInterpretation.planet2 == planet2,
        AspectInterpretation.aspect_type == aspect_type
    ).first()
    
    # If not found, try reverse order
    if not interpretation:
        interpretation = db.query(AspectInterpretation).filter(
            AspectInterpretation.planet1 == planet2,
            AspectInterpretation.planet2 == planet1,
            AspectInterpretation.aspect_type == aspect_type
        ).first()
    
    if interpretation:
        return interpretation.interpretation
    
    return f"No interpretation available for {planet1} {aspect_type} {planet2}."


def get_template(db: Session, template_name: str) -> Optional[str]:
    """
    Get interpretation template by name
    
    Args:
        db: Database session
        template_name: Template name
        
    Returns:
        Template content or None if not found
    """
    template = db.query(InterpretationTemplate).filter(
        InterpretationTemplate.name == template_name
    ).first()
    
    if template:
        return template.template_content
    
    # Default template if not found
    return """# Natal Chart Interpretation

**Birth Information:**
- Date: {{ birth_info.birth_date }}
- Time: {{ birth_info.birth_time }}
- Coordinates: {{ birth_info.latitude }}° {{ 'N' if birth_info.latitude >= 0 else 'S' }}, {{ birth_info.longitude }}° {{ 'E' if birth_info.longitude >= 0 else 'W' }}
- Timezone: {{ birth_info.timezone }}

## Planetary Positions
{% for planet in planets %}
- {{ planet.name }} in {{ planet.sign }} ({{ planet.house }}{{ 'st' if planet.house == 1 else 'nd' if planet.house == 2 else 'rd' if planet.house == 3 else 'th' }} house)
{% endfor %}

## Major Aspects
{% for aspect in major_aspects %}
- {{ aspect.planet1 }} {{ aspect.aspect_type }} {{ aspect.planet2 }} (orb: {{ aspect.orb|round(1) }}°)
{% endfor %}
"""


def get_ascendant_keywords(sign: str) -> str:
    """
    Get keywords for ascendant by sign
    
    Args:
        sign: Zodiac sign
        
    Returns:
        Keywords string
    """
    keywords = {
        "Aries": "direct, assertive, and action-oriented",
        "Taurus": "steady, reliable, and sensually attuned",
        "Gemini": "communicative, curious, and intellectually adaptable",
        "Cancer": "nurturing, protective, and emotionally receptive",
        "Leo": "charismatic, proud, and warmly expressive",
        "Virgo": "analytical, detail-oriented, and helpful",
        "Libra": "diplomatic, harmonious, and socially polished",
        "Scorpio": "intense, private, and magnetically powerful",
        "Sagittarius": "optimistic, expansive, and philosophically minded",
        "Capricorn": "dignified, structured, and achievement-oriented",
        "Aquarius": "unconventional, forward-thinking, and socially conscious",
        "Pisces": "impressionable, empathic, and dreamy"
    }
    
    return keywords.get(sign, "distinctive and unique")


def render_interpretation(
    db: Session,
    chart_data: Dict[str, Any],
    birth_info: Dict[str, Any],
    template_name: str = "basic_text"
) -> str:
    """
    Render a complete chart interpretation using template
    
    Args:
        db: Database session
        chart_data: Complete chart data dictionary
        birth_info: Birth information dictionary
        template_name: Template name to use
        
    Returns:
        Rendered interpretation text
    """
    # Get template content
    template_content = get_template(db, template_name)
    
    # Create Jinja2 template
    template = jinja2.Template(template_content)
    
    # Get sun and moon data
    sun = get_planet_by_name(chart_data["planets"], "Sun")
    moon = get_planet_by_name(chart_data["planets"], "Moon")
    
    # Get interpretations for sun and moon
    sun_sign_interpretation = get_planet_sign_interpretation(db, "Sun", sun["sign"]) if sun else ""
    moon_sign_interpretation = get_planet_sign_interpretation(db, "Moon", moon["sign"]) if moon else ""
    
    # Get ascendant keywords
    ascendant = chart_data["angles"]["ascendant"]
    ascendant_keywords = get_ascendant_keywords(ascendant["sign"])
    
    # Filter for major aspects
    major_aspects = filter_major_aspects(chart_data["aspects"])
    
    # Create interpretation context
    context = {
        "birth_info": birth_info,
        "chart_data": chart_data,
        "planets": chart_data["planets"],
        "houses": chart_data["houses"],
        "aspects": chart_data["aspects"],
        "angles": chart_data["angles"],
        "sun": sun,
        "moon": moon,
        "ascendant": ascendant,
        "sun_sign_interpretation": sun_sign_interpretation,
        "moon_sign_interpretation": moon_sign_interpretation,
        "ascendant_keywords": ascendant_keywords,
        "major_aspects": major_aspects
    }
    
    # Render template
    return template.render(**context)
