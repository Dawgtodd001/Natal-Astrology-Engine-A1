"""
Utility functions for the Flask frontend
"""
import os
import time
import logging
import requests
from urllib.parse import urljoin
from flask import flash, current_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get configuration from environment or use defaults
API_BASE_URL = os.environ.get("API_BASE_URL") or "http://localhost:8000"
API_KEY = os.environ.get("DEFAULT_API_KEY") or "test_key_1234567890"

logger.info(f"Using API endpoint: {API_BASE_URL}")

def check_api_health():
    """Check if the API is healthy before making requests"""
    try:
        # The health endpoint might be at /api/health or /api/api/health depending on the router configuration
        # Try both paths
        try:
            response = requests.get(urljoin(API_BASE_URL, '/api/health'), timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
            
        # Also try another path format if the first one fails
        response = requests.get(urljoin(API_BASE_URL, '/api/api/health'), timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

def api_request(endpoint, data=None, method="POST", retry_count=3, retry_delay=0.5):
    """
    Make API request with retry logic
    
    Args:
        endpoint: API endpoint (without leading slash)
        data: JSON data to send
        method: HTTP method (POST, GET, etc.)
        retry_count: Number of retries on failure
        retry_delay: Delay between retries in seconds
        
    Returns:
        Response JSON or text depending on endpoint, or None if failed
    """
    if not check_api_health():
        logger.error("API service unavailable, health check failed")
        return None
    
    # Make sure we're using the right path for the API
    url = urljoin(API_BASE_URL, f'/api/{endpoint}')
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    
    for attempt in range(retry_count):
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=data, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=10)
                
            response.raise_for_status()
            
            # Special case for the interpret endpoint which returns plain text
            if endpoint == 'interpret':
                return response.text
            else:
                return response.json()
                
        except requests.RequestException as e:
            logger.warning(f"API request attempt {attempt+1}/{retry_count} failed: {e}")
            if attempt == retry_count - 1:
                logger.error(f"API request failed after {retry_count} attempts: {e}")
                return None
            time.sleep(retry_delay)
    
    return None