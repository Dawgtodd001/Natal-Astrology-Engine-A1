"""
Monitoring utilities for the Natal Astrology Web Interface
"""
import os
import time
import logging
from typing import Dict, Any, Optional
from functools import wraps

import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import request, Response, Flask

logger = logging.getLogger(__name__)

# Initialize Prometheus metrics
REQUEST_COUNT = Counter(
    'natal_web_requests_total', 
    'Total number of web requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'natal_web_request_latency_seconds', 
    'Request latency in seconds',
    ['method', 'endpoint']
)

API_REQUEST_COUNT = Counter(
    'natal_api_requests_from_web_total', 
    'Total number of API requests from web interface',
    ['api_endpoint', 'status_code']
)

API_REQUEST_LATENCY = Histogram(
    'natal_api_request_from_web_latency_seconds', 
    'API request latency from web interface in seconds',
    ['api_endpoint']
)

# Cache metrics
CACHE_HIT_COUNT = Counter(
    'natal_cache_hit_total',
    'Total number of cache hits',
    ['cache_type']
)

CACHE_MISS_COUNT = Counter(
    'natal_cache_miss_total',
    'Total number of cache misses',
    ['cache_type']
)

CACHE_STATUS = Gauge(
    'natal_cache_up',
    'Redis cache status (1=up, 0=down)',
    ['cache_instance']
)

CACHE_OPERATIONS = Counter(
    'natal_cache_operations_total',
    'Total number of cache operations',
    ['operation', 'status']
)

def setup_metrics(app: Flask):
    """Add Prometheus metrics to Flask app"""
    
    @app.route('/metrics')
    def metrics():
        """Endpoint to expose Prometheus metrics"""
        return Response(
            generate_latest(),
            mimetype=CONTENT_TYPE_LATEST
        )
        
    @app.route('/health')
    def health():
        """Health check endpoint"""
        from utils import check_api_health
        
        # Check API status
        api_status = check_api_health()
        
        # Check Redis status
        redis_status = False
        try:
            import redis
            import os
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = redis.from_url(redis_url)
            redis_status = redis_client.ping()
            # Update cache status metric
            CACHE_STATUS.labels('redis-main').set(1 if redis_status else 0)
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            # Update cache status metric on failure
            CACHE_STATUS.labels('redis-main').set(0)
        
        # Overall status is UP only if both API and Redis are UP
        status = "UP" if (api_status and redis_status) else "DOWN"
        
        response = {
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "services": {
                "web": "UP",
                "api": "UP" if api_status else "DOWN",
                "redis": "UP" if redis_status else "DOWN"
            }
        }
        
        return response, 200 if status == "UP" else 503

    @app.before_request
    def before_request():
        """Record request timestamp before each request"""
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Record metrics after each request"""
        # Skip metrics endpoint to avoid recursion
        if request.path != '/metrics':
            request_latency = time.time() - getattr(request, 'start_time', time.time())
            
            # Record request count and latency
            REQUEST_COUNT.labels(
                request.method, 
                request.path, 
                response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                request.method, 
                request.path
            ).observe(request_latency)
        
        return response

def track_api_request(func):
    """Decorator to track API requests from the web interface"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        endpoint = kwargs.get('endpoint', 'unknown')
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # Record metrics for successful call
            api_latency = time.time() - start_time
            
            # Extract status code from result if possible, default to 200
            status_code = 200
            if isinstance(result, tuple) and len(result) > 1 and isinstance(result[0], dict):
                status_code = result[0].get('status_code', 200)
            
            API_REQUEST_COUNT.labels(
                endpoint,
                status_code
            ).inc()
            
            API_REQUEST_LATENCY.labels(
                endpoint
            ).observe(api_latency)
            
            return result
            
        except Exception as e:
            # Record metrics for failed call
            api_latency = time.time() - start_time
            
            API_REQUEST_COUNT.labels(
                endpoint,
                500  # Assuming exception = server error
            ).inc()
            
            API_REQUEST_LATENCY.labels(
                endpoint
            ).observe(api_latency)
            
            # Re-raise the exception
            raise
    
    return wrapper