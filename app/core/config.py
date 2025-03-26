"""
Configuration for the astrological engine
"""
import os
from typing import Dict, Any, List

# Application configuration
APP_NAME = "Natal Astrology Engine"
VERSION = "1.0.0"
DESCRIPTION = "API for generating and interpreting astrological birth charts"

# List of planets to calculate
PLANETS = [
    "Sun", 
    "Moon", 
    "Mercury", 
    "Venus", 
    "Mars", 
    "Jupiter", 
    "Saturn", 
    "Uranus", 
    "Neptune", 
    "Pluto",
    "North Node"
]

# List of aspects to calculate
ASPECTS = {
    "conjunction": {"angle": 0, "orb": 8, "major": True},
    "sextile": {"angle": 60, "orb": 6, "major": True},
    "square": {"angle": 90, "orb": 8, "major": True},
    "trine": {"angle": 120, "orb": 8, "major": True},
    "opposition": {"angle": 180, "orb": 8, "major": True},
    "semisextile": {"angle": 30, "orb": 3, "major": False},
    "semisquare": {"angle": 45, "orb": 3, "major": False},
    "sesquisquare": {"angle": 135, "orb": 3, "major": False},
    "quincunx": {"angle": 150, "orb": 5, "major": False},
}

# Zodiac signs
ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces"
]

# House systems
HOUSE_SYSTEMS = {
    "placidus": "Placidus",
    "whole_sign": "Whole Sign",
    "equal": "Equal Houses",
    "koch": "Koch",
    "regiomontanus": "Regiomontanus",
    "campanus": "Campanus",
    "porphyry": "Porphyry",
    "morinus": "Morinus",
    "polich_page": "Polich-Page (Topocentric)",
    "topocentric": "Topocentric",
    "alcabitius": "Alcabitius"
}

# Element and modality mappings for signs
SIGN_ELEMENTS = {
    "Aries": "Fire",
    "Leo": "Fire",
    "Sagittarius": "Fire",
    "Taurus": "Earth",
    "Virgo": "Earth",
    "Capricorn": "Earth",
    "Gemini": "Air",
    "Libra": "Air",
    "Aquarius": "Air",
    "Cancer": "Water",
    "Scorpio": "Water",
    "Pisces": "Water"
}

SIGN_MODALITIES = {
    "Aries": "Cardinal",
    "Cancer": "Cardinal",
    "Libra": "Cardinal",
    "Capricorn": "Cardinal",
    "Taurus": "Fixed",
    "Leo": "Fixed",
    "Scorpio": "Fixed",
    "Aquarius": "Fixed",
    "Gemini": "Mutable",
    "Virgo": "Mutable",
    "Sagittarius": "Mutable",
    "Pisces": "Mutable"
}
