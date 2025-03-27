"""
Monitoring utilities for the Natal Astrology Web Interface
"""

import time
import functools
from flask import Flask, request, Response, g
import logging

# Try importing prometheus_client and setup multiprocessing mode if available
try:
    import prometheus_client
    from prometheus_client import multiprocess, Counter, Histogram, Gauge, Summary, REGISTRY
    
    # Setup multiprocessing mode if PROMETHEUS_MULTIPROC_DIR is defined
    import os
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        prometheus_dir = os.environ["PROMETHEUS_MULTIPROC_DIR"]
        if not os.path.exists(prometheus_dir):
            os.makedirs(prometheus_dir)
        multiprocess.MultiProcessCollector(REGISTRY)
    
    # Define metrics
    REQUEST_COUNT = Counter(
        'web_request_total',
        'Total number of HTTP requests',
        ['method', 'endpoint', 'status']
    )
    
    REQUEST_LATENCY = Histogram(
        'web_request_duration_seconds',
        'HTTP request latency in seconds',
        ['method', 'endpoint']
    )
    
    API_REQUEST_COUNT = Counter(
        'api_request_total',
        'Total number of API requests from web interface',
        ['endpoint', 'status']
    )
    
    CACHE_HIT_COUNT = Counter(
        'cache_hit_total',
        'Total number of cache hits',
        ['type']
    )
    
    CACHE_MISS_COUNT = Counter(
        'cache_miss_total',
        'Total number of cache misses',
        ['type']
    )
    
    CACHE_OPERATIONS = Counter(
        'cache_operations_total',
        'Total number of cache operations',
        ['operation', 'result']
    )
    
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    
logger = logging.getLogger(__name__)


def setup_metrics(app: Flask):
    """Add Prometheus metrics to Flask app"""
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not available, skipping metrics setup")
        return
    
    # Add metrics endpoint
    @app.route('/metrics')
    def metrics():
        """Endpoint to expose Prometheus metrics"""
        return Response(
            prometheus_client.generate_latest(), 
            mimetype='text/plain'
        )
    
    # Add health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint"""
        # Check API availability
        api_available = getattr(g, 'api_available', False)
        
        # Check Redis availability if Redis client exists
        try:
            from app.utils.redis_client import get_redis
            redis_client = get_redis()
            redis_available = redis_client is not None and redis_client.ping()
        except (ImportError, Exception):
            redis_available = False
        
        # Construct response
        response = {
            'status': 'ok' if api_available else 'degraded',
            'api': 'available' if api_available else 'unavailable',
            'redis': 'available' if redis_available else 'unavailable'
        }
        
        status_code = 200 if api_available else 503
        return response, status_code
    
    # Register before_request handler
    @app.before_request
    def before_request():
        """Record request timestamp before each request"""
        g.start_time = time.time()
    
    # Register after_request handler
    @app.after_request
    def after_request(response):
        """Record metrics after each request"""
        # Skip metrics for the metrics endpoint
        if request.path == "/metrics":
            return response
        
        # Calculate request duration
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Normalize route by replacing route parameters with placeholders
            if hasattr(request, 'endpoint') and request.endpoint:
                endpoint = request.endpoint
            else:
                endpoint = request.path
            
            # Track request count and latency
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
        
        return response


def track_api_request(func):
    """Decorator to track API requests from the web interface"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not PROMETHEUS_AVAILABLE:
            return func(*args, **kwargs)
        
        endpoint = func.__name__
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            status = "success"
        except Exception as e:
            status = "error"
            raise e
        finally:
            # Track API request
            API_REQUEST_COUNT.labels(
                endpoint=endpoint,
                status=status
            ).inc()
        
        return result
    
    return wrapper