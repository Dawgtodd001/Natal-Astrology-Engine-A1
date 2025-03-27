"""
API client utilities for service communication
"""
import os
import json
import time
import logging
import requests
from typing import Any, Dict, List, Optional, Tuple, Union

# Set up logging
logger = logging.getLogger(__name__)

# Load settings
from shared.config.settings import settings

# Default timeout in seconds
DEFAULT_TIMEOUT = 10.0


def check_api_health(max_retries=5, initial_delay=1.0, timeout=2.0) -> bool:
    """
    Check if the API is healthy before making requests
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds (will increase with exponential backoff)
        timeout: Request timeout in seconds
        
    Returns:
        bool: True if API is healthy, False otherwise
    """
    # Get API URL from settings
    api_url = settings.API_GATEWAY_URL
    health_endpoint = f"{api_url}/api/health"
    
    for attempt in range(max_retries):
        try:
            # Calculate delay with exponential backoff
            delay = initial_delay * (2 ** attempt)
            
            # Make health check request
            response = requests.get(health_endpoint, timeout=timeout)
            
            # Check if response is success
            if response.status_code == 200:
                health_data = response.json()
                
                if health_data.get("status") == "ok":
                    logger.info(f"API health check successful after {attempt + 1} attempts")
                    return True
                else:
                    logger.warning(f"API reported unhealthy status: {health_data}")
            else:
                logger.warning(f"API health check failed with status {response.status_code}")
                
            # Wait before retrying
            logger.info(f"Retrying API health check in {delay:.1f} seconds (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
            
        except requests.RequestException as e:
            # Connection error, retry after delay
            logger.warning(f"API health check request failed: {str(e)}")
            logger.info(f"Retrying API health check in {initial_delay * (2 ** attempt):.1f} seconds (attempt {attempt + 1}/{max_retries})")
            time.sleep(initial_delay * (2 ** attempt))
            
    # All retries failed
    logger.error(f"API health check failed after {max_retries} attempts")
    return False


def api_request(
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    method: str = "POST",
    retry_count: int = 3,
    retry_delay: float = 0.5,
    timeout: float = DEFAULT_TIMEOUT,
    include_error_details: bool = False
) -> Union[Any, Tuple[Any, Optional[Dict[str, Any]]]]:
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
    # Get API URL from settings
    api_url = settings.API_GATEWAY_URL
    
    # Ensure endpoint doesn't start with slash
    if endpoint.startswith('/'):
        endpoint = endpoint[1:]
        
    # Build full URL
    url = f"{api_url}/api/{endpoint}"
    
    # Default headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-API-Key": os.environ.get("DEFAULT_API_KEY") or "test_key_1234567890",
    }
    
    # Add a service identifier to help track inter-service requests
    headers["X-Service-Source"] = "web"
    
    # Setup error info dictionary
    error_info = None
    
    for attempt in range(retry_count + 1):  # +1 because we want to do the initial attempt plus retries
        try:
            start_time = time.time()
            
            # Make the request
            if method.upper() == "GET":
                response = requests.get(url, params=data, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, json=data, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            # Log request for debugging (careful not to log sensitive data)
            logger.debug(f"API {method} {url} completed in {time.time() - start_time:.3f}s with status {response.status_code}")
            
            # Check response status
            if response.ok:
                # Check if response is JSON
                try:
                    result = response.json()
                except ValueError:
                    # Not JSON, return text for some endpoints
                    result = response.text
                    
                # Return result based on include_error_details flag
                if include_error_details:
                    return result, None
                else:
                    return result
            else:
                # Request failed, log the error
                error_msg = f"API request failed: {response.status_code} - {response.reason}"
                try:
                    error_content = response.json()
                    error_msg += f" - {error_content.get('detail') or error_content}"
                    
                    # Update error info
                    error_info = {
                        "error_type": "HTTPError",
                        "status_code": response.status_code,
                        "error_message": error_content.get('detail') or error_content.get('message', error_content),
                        "content": error_content
                    }
                except ValueError:
                    error_msg += f" - {response.text[:100]}..."
                    
                    # Update error info
                    error_info = {
                        "error_type": "HTTPError",
                        "status_code": response.status_code,
                        "error_message": response.text[:200],
                        "content": response.text
                    }
                    
                logger.warning(error_msg)
                
                # Handle specific error codes
                if response.status_code == 429:  # Too Many Requests
                    retry_delay_time = float(response.headers.get('Retry-After', retry_delay * 2))
                    logger.info(f"Rate limit hit, retrying in {retry_delay_time}s")
                    time.sleep(retry_delay_time)
                elif response.status_code >= 500:  # Server error, worth retrying
                    if attempt < retry_count:
                        logger.info(f"Retrying in {retry_delay}s (attempt {attempt+1}/{retry_count})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(f"API request failed after {retry_count} retries")
                else:  # 4xx errors generally shouldn't be retried
                    break
                    
        except requests.Timeout as e:
            # Timeout, retry with exponential backoff
            logger.warning(f"API request timed out: {str(e)}")
            
            # Update error info
            error_info = {
                "error_type": "ReadTimeout" if "Read timed out" in str(e) else "ConnectTimeout",
                "error_message": str(e)
            }
            
            if attempt < retry_count:
                logger.info(f"Retrying in {retry_delay}s (attempt {attempt+1}/{retry_count})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"API request timed out after {retry_count} retries")
                
        except requests.RequestException as e:
            # Connection error, retry with exponential backoff
            logger.warning(f"API request failed: {str(e)}")
            
            # Update error info
            error_info = {
                "error_type": e.__class__.__name__,
                "error_message": str(e)
            }
            
            if attempt < retry_count:
                logger.info(f"Retrying in {retry_delay}s (attempt {attempt+1}/{retry_count})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"API request failed after {retry_count} retries")
                
        except Exception as e:
            # Unexpected error
            logger.exception(f"Unexpected error in API request: {str(e)}")
            
            # Update error info
            error_info = {
                "error_type": "UnexpectedError",
                "error_message": str(e)
            }
            
            break
            
    # If we get here, all retries failed or a non-retryable error occurred
    if error_info is None:
        error_info = {
            "error_type": "ServiceUnavailable",
            "error_message": "Service is unavailable or unreachable"
        }
        
    # Return based on include_error_details flag
    if include_error_details:
        return None, error_info
    else:
        return None