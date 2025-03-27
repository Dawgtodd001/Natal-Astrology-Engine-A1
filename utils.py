"""
Utility functions for the Flask frontend
"""
import os
import time
import logging
import random
import requests
from urllib.parse import urljoin
from flask import flash, current_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get configuration from environment or use defaults
# In Replit, we'll hardcode the URL to localhost:8000 since we know that's where the FastAPI runs
API_BASE_URL = "http://localhost:8000"
API_KEY = os.environ.get("DEFAULT_API_KEY") or "test_key_1234567890"

logger.info(f"Using API endpoint: {API_BASE_URL}")

def check_api_health(max_retries=5, initial_delay=1.0):
    """
    Check if the API is healthy before making requests
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds (will increase with exponential backoff)
        
    Returns:
        bool: True if API is healthy, False otherwise
    """
    url = f"{API_BASE_URL}/api/health"
    logger.info(f"Checking API health at: {url}")
    
    # Implement retry with exponential backoff
    current_retry = 0
    current_delay = initial_delay
    
    while current_retry < max_retries:
        try:
            # Set a reasonable timeout for the connection
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                logger.info("API health check successful")
                return True
            else:
                logger.warning(f"API health check failed: Unexpected status code {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"API health check failed (attempt {current_retry+1}/{max_retries}): {e}")
        except Exception as e:
            logger.warning(f"API health check failed with unexpected error: {e}")
        
        # Increment retry counter
        current_retry += 1
        
        # If we've exhausted all retries, return False
        if current_retry >= max_retries:
            logger.error(f"API health check failed after {max_retries} attempts")
            return False
            
        # Wait with exponential backoff before the next attempt
        logger.info(f"Retrying in {current_delay:.1f} seconds...")
        time.sleep(current_delay)
        
        # Increase the delay for the next retry (exponential backoff with jitter)
        current_delay = min(initial_delay * (2 ** current_retry) + random.uniform(0, 0.5), 10.0)
    
    # Should never reach here, but just in case
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
    # For the first request, check API health
    if not check_api_health():
        logger.error("API service unavailable, health check failed")
        return None
    
    # Construct the API URL
    url = f"{API_BASE_URL}/api/{endpoint}"
        
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