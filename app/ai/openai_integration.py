"""
OpenAI API integration for generating chart interpretations
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Union

import openai
from app.utils.logging import get_logger

# For async operation tracking
from celery.result import AsyncResult

logger = get_logger(__name__)

def validate_openai_api_key() -> bool:
    """
    Validate that the OpenAI API key is set and valid
    
    Returns:
        bool: True if the key is valid, False otherwise
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logger.warning("OpenAI API key not found in environment variables")
        return False
        
    try:
        # Set the API key
        openai.api_key = api_key
        
        # Make a simple request to validate the key
        openai.models.list()
        logger.info("OpenAI API key validated successfully")
        return True
    except Exception as e:
        logger.error(f"Error validating OpenAI API key: {str(e)}")
        return False

def generate_chart_interpretation(
    chart_data: Dict[str, Any],
    birth_info: Dict[str, Any],
    style: Optional[str] = "detailed",
    async_mode: bool = False
) -> Union[str, AsyncResult]:
    """
    Generate an AI-powered interpretation of the birth chart
    
    Args:
        chart_data: Complete chart data dictionary
        birth_info: Birth information dictionary
        style: Style of interpretation ("concise", "detailed", "spiritual", "psychological")
        async_mode: If True, returns a Celery AsyncResult; if False, returns the result directly
        
    Returns:
        Rendered interpretation text or AsyncResult if async_mode=True
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return "Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    
    # Set the API key
    openai.api_key = api_key
    
    # Format chart data for the prompt
    planets_info = "\n".join([
        f"- {planet['name']}: {planet['sign']} at {planet['degree']}°{planet['minutes']}', " + 
        f"in House {planet['house']}{' (Retrograde)' if planet.get('retrograde') else ''}"
        for planet in chart_data.get('planets', [])
    ])
    
    houses_info = "\n".join([
        f"- House {house['number']}: {house['sign']} at {house['degree']}°{house['minutes']}'"
        for house in chart_data.get('houses', [])
    ])
    
    aspects_info = "\n".join([
        f"- {aspect['planet1']} {aspect['aspect_type']} {aspect['planet2']} " + 
        f"(orb: {aspect['orb']:.2f}°, {'applying' if aspect.get('applying') else 'separating'})"
        for aspect in chart_data.get('aspects', [])
    ])
    
    angles_info = ""
    if 'angles' in chart_data:
        angles = chart_data['angles']
        for angle_name, angle_data in angles.items():
            angles_info += f"- {angle_name.capitalize()}: {angle_data['sign']} at {angle_data['degree']}°{angle_data['minutes']}'\n"
    
    # Create birth info text
    birth_details = f"""
Birth Information:
- Date: {birth_info.get('birth_date', 'Unknown')}
- Time: {birth_info.get('birth_time', 'Unknown')}
- Location: Latitude {birth_info.get('latitude', 'Unknown')}, Longitude {birth_info.get('longitude', 'Unknown')}
- Timezone: {birth_info.get('timezone', 'Unknown')}
- House System: {birth_info.get('house_system', 'placidus').capitalize()}
    """
    
    # Determine temperature and complexity based on style
    temperature = 0.7  # Default
    
    if style == "concise":
        temperature = 0.5
        focus_text = "Focus on providing a brief, to-the-point summary of the most important chart features."
        max_tokens = 800
    elif style == "spiritual":
        temperature = 0.8
        focus_text = "Focus on spiritual growth, soul purpose, and karmic lessons revealed in this chart."
        max_tokens = 1500
    elif style == "psychological":
        temperature = 0.7
        focus_text = "Focus on psychological patterns, personality traits, motivations, and potential challenges."
        max_tokens = 1500
    else:  # detailed
        temperature = 0.7
        focus_text = "Provide a comprehensive astrological analysis covering all major chart components."
        max_tokens = 2000
    
    # Create the prompt
    prompt = f"""
You are an expert astrologer with deep knowledge of natal chart interpretation.
Analyze the following birth chart and provide a {style} interpretation.
{focus_text}

{birth_details}

Chart Information:
1. Planets:
{planets_info}

2. Houses:
{houses_info}

3. Aspects:
{aspects_info}

4. Angles:
{angles_info}

Structure your interpretation with clear sections and highlight the most significant placements and aspects.
Include both strengths and potential challenges.
Provide specific, personalized insights based on the unique configuration of this chart.
"""

    # If async_mode is True, we'll delegate to Celery task
    if async_mode:
        from app.celery_app import celery_app
        logger.info(f"Delegating {style} chart interpretation to Celery task")
        task = celery_app.send_task(
            'app.tasks.interpretation_tasks.generate_chart_interpretation',
            args=[chart_data, birth_info, style]
        )
        return task
    
    try:
        # Generate interpretation using OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert astrologer with decades of experience interpreting natal charts."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        # Extract and return the interpretation
        interpretation = response.choices[0].message.content
        
        # Log success but not the full interpretation (could be very long)
        logger.info(f"Generated {style} AI interpretation successfully")
        return interpretation
        
    except Exception as e:
        error_msg = f"Error generating OpenAI interpretation: {str(e)}"
        logger.error(error_msg)
        return f"Error generating AI-powered interpretation: {str(e)}"

def generate_transit_interpretation(
    natal_chart: Dict[str, Any],
    transit_chart: Dict[str, Any],
    transit_aspects: List[Dict[str, Any]],
    birth_info: Dict[str, Any],
    transit_info: Dict[str, Any],
    style: Optional[str] = "detailed",
    async_mode: bool = False
) -> Union[str, AsyncResult]:
    """
    Generate an AI-powered interpretation of transit aspects to a natal chart
    
    Args:
        natal_chart: Natal chart data dictionary
        transit_chart: Transit chart data dictionary
        transit_aspects: List of transit-to-natal aspect dictionaries
        birth_info: Birth information dictionary
        transit_info: Transit date information dictionary
        style: Style of interpretation ("concise", "detailed", "predictive", "growth")
        async_mode: If True, returns a Celery AsyncResult; if False, returns the result directly
        
    Returns:
        Rendered interpretation text or AsyncResult if async_mode=True
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return "Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    
    # Set the API key
    openai.api_key = api_key
    
    # Format natal chart data
    natal_planets_info = "\n".join([
        f"- {planet['name']}: {planet['sign']} at {planet['degree']}°{planet['minutes']}', " + 
        f"in House {planet['house']}{' (Retrograde)' if planet.get('retrograde') else ''}"
        for planet in natal_chart.get('planets', [])
    ])
    
    # Format transit chart data
    transit_planets_info = "\n".join([
        f"- {planet['name']}: {planet['sign']} at {planet['degree']}°{planet['minutes']}'" + 
        f"{' (Retrograde)' if planet.get('retrograde') else ''}"
        for planet in transit_chart.get('planets', [])
    ])
    
    # Format transit aspects
    transit_aspects_info = "\n".join([
        f"- Transit {aspect['from_planet']} {aspect['aspect_type']} Natal {aspect['to_planet']} " + 
        f"(orb: {aspect['orb']:.2f}°, {'applying' if aspect.get('applying') else 'separating'})"
        for aspect in transit_aspects
    ])
    
    # Create birth and transit info text
    birth_details = f"""
Birth Information:
- Date: {birth_info.get('birth_date', 'Unknown')}
- Time: {birth_info.get('birth_time', 'Unknown')}
- Location: Latitude {birth_info.get('latitude', 'Unknown')}, Longitude {birth_info.get('longitude', 'Unknown')}
    """
    
    transit_details = f"""
Transit Information:
- Date: {transit_info.get('transit_date', 'Unknown')}
- Time: {transit_info.get('transit_time', 'Unknown')}
- Location: Latitude {transit_info.get('transit_latitude', 'Unknown')}, Longitude {transit_info.get('transit_longitude', 'Unknown')}
    """
    
    # Determine temperature and complexity based on style
    temperature = 0.7  # Default
    
    if style == "concise":
        temperature = 0.5
        focus_text = "Focus on providing a brief, to-the-point summary of the most important transit influences."
        max_tokens = 800
    elif style == "predictive":
        temperature = 0.8
        focus_text = "Focus on potential events, developments, and timing of significant transit influences."
        max_tokens = 1500
    elif style == "growth":
        temperature = 0.7
        focus_text = "Focus on personal growth opportunities, lessons, and how to harness these transit energies constructively."
        max_tokens = 1500
    else:  # detailed
        temperature = 0.7
        focus_text = "Provide a comprehensive analysis of how these transits interact with the natal chart."
        max_tokens = 2000
    
    # Create the prompt
    prompt = f"""
You are an expert astrologer with deep knowledge of transit interpretations.
Analyze the following natal chart and current transits to provide a {style} interpretation.
{focus_text}

{birth_details}

{transit_details}

Natal Chart Planets:
{natal_planets_info}

Current Transit Positions:
{transit_planets_info}

Transit-to-Natal Aspects:
{transit_aspects_info}

Structure your interpretation with clear sections and highlight the most significant transit influences.
Focus on current and upcoming transits, their duration, and potential manifestations.
Provide specific, personalized insights on how these transits might affect the native.
"""

    # If async_mode is True, we'll delegate to Celery task
    if async_mode:
        from app.celery_app import celery_app
        logger.info(f"Delegating {style} transit interpretation to Celery task")
        task = celery_app.send_task(
            'app.tasks.interpretation_tasks.generate_transit_interpretation',
            args=[natal_chart, transit_chart, transit_aspects, birth_info, transit_info, style]
        )
        return task
        
    try:
        # Generate interpretation using OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert astrologer with decades of experience interpreting transits."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        # Extract and return the interpretation
        interpretation = response.choices[0].message.content
        
        # Log success but not the full interpretation (could be very long)
        logger.info(f"Generated {style} transit interpretation successfully")
        return interpretation
        
    except Exception as e:
        error_msg = f"Error generating OpenAI transit interpretation: {str(e)}"
        logger.error(error_msg)
        return f"Error generating AI-powered transit interpretation: {str(e)}"