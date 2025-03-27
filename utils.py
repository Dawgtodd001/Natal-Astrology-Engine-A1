"""
Utility functions for the Flask frontend
"""
import os
import time
import uuid
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

def api_request(endpoint, data=None, method="POST", retry_count=3, retry_delay=0.5, timeout=10, include_error_details=False):
    """
    Make API request with retry logic and enhanced error handling
    
    Args:
        endpoint: API endpoint (without leading slash)
        data: JSON data to send
        method: HTTP method (POST, GET, etc.)
        retry_count: Number of retries on failure
        retry_delay: Delay between retries in seconds
        timeout: Request timeout in seconds
        include_error_details: If True, returns a tuple (data, error_info) where error_info contains details if request failed
        
    Returns:
        - If include_error_details=False (default): Response JSON/text depending on endpoint, or None if failed
        - If include_error_details=True: Tuple (response_data, error_info) where error_info is None on success or
          a dict with error details on failure
    """

    # For the first request, check API health
    if not check_api_health():
        error_info = {
            "error_type": "ServiceUnavailable",
            "error_message": "API service unavailable, health check failed",
            "status_code": 503
        }
        logger.error("API service unavailable, health check failed")
        return (None, error_info) if include_error_details else None
    
    # Construct the API URL
    url = f"{API_BASE_URL}/api/{endpoint}"
    
    # Track performance metrics
    start_time = time.time()
    metrics = {"endpoint": endpoint, "method": method}
    
    # Set up headers with request ID for tracing
    request_id = str(uuid.uuid4())
    headers = {
        "X-API-Key": API_KEY, 
        "Content-Type": "application/json",
        "X-Request-ID": request_id
    }
    
    # Initialize error info
    error_info = None
    response_data = None
    
    # Use exponential backoff with jitter for retries
    for attempt in range(retry_count):
        try:
            # Make request with appropriate method
            if method.upper() == "GET":
                response = requests.get(url, params=data, headers=headers, timeout=timeout)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            
            # Track response time
            response_time = time.time() - start_time
            metrics["response_time"] = round(response_time * 1000, 2)  # ms
            
            # Update metrics with status code
            metrics["status_code"] = response.status_code
            
            # Check for error responses
            if response.status_code >= 400:
                # Try to parse error details from JSON response
                try:
                    error_details = response.json()
                    error_message = error_details.get('detail', f"API error: HTTP {response.status_code}")
                    error_code = error_details.get('error_code', 'UNKNOWN')
                    
                    error_info = {
                        "error_type": "HTTPError",
                        "error_message": error_message,
                        "error_code": error_code,
                        "status_code": response.status_code,
                        "request_id": request_id
                    }
                except ValueError:
                    # Non-JSON error response
                    error_info = {
                        "error_type": "HTTPError",
                        "error_message": f"API error: HTTP {response.status_code} - {response.text[:100]}",
                        "status_code": response.status_code,
                        "request_id": request_id
                    }
                
                # For client errors (4xx), don't retry
                if 400 <= response.status_code < 500:
                    log_level = "warning"
                    log_msg = f"API client error ({response.status_code}) in {method} {endpoint}"
                    # Don't retry client errors
                    break
                else:
                    # For server errors (5xx), retry with backoff
                    log_level = "error"
                    log_msg = f"API server error ({response.status_code}) in {method} {endpoint}, will retry"
                    
                # Log the error at appropriate level
                getattr(logger, log_level)(log_msg, extra={
                    "error_info": error_info,
                    "metrics": metrics,
                    "attempt": attempt + 1
                })
                
                # For server errors, continue to retry logic
                response.raise_for_status()  # This will raise an exception for server errors
            
            # Process successful response
            if endpoint == 'interpret':
                # Special case for interpret endpoint which returns plain text
                response_data = response.text
            else:
                # JSON response for other endpoints
                response_data = response.json()
                
            # Log successful request
            logger.info(f"API request successful: {method} {endpoint}", extra={
                "metrics": metrics,
                "request_id": request_id
            })
            
            # Return the data
            return (response_data, None) if include_error_details else response_data
                
        except requests.RequestException as e:
            # Calculate retry delay with exponential backoff and jitter
            backoff_delay = retry_delay * (2 ** attempt)
            jitter = random.uniform(0, 0.1 * backoff_delay)  # 10% jitter
            actual_delay = backoff_delay + jitter
            
            # Update error info
            error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "attempt": attempt + 1,
                "request_id": request_id
            }
            
            # Check if this is the last attempt
            if attempt == retry_count - 1:
                logger.error(f"API request failed after {retry_count} attempts: {e}", extra={
                    "error_info": error_info,
                    "metrics": metrics,
                    "endpoint": endpoint
                })
                return (None, error_info) if include_error_details else None
            
            # Log warning and retry
            logger.warning(f"API request attempt {attempt+1}/{retry_count} failed: {e}", extra={
                "error_info": error_info,
                "retry_delay": round(actual_delay, 2),
                "endpoint": endpoint
            })
            
            # Sleep before retry
            time.sleep(actual_delay)
    
    return None