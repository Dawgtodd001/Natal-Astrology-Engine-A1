"""
Prometheus metrics utilities for monitoring and observability

This module provides standardized metrics collection across all services
"""
import os
import time
import logging
import threading
from typing import Optional, Dict, Any, Callable

# Set up logging
logger = logging.getLogger(__name__)

# Try to import Prometheus client with fallback
try:
    import prometheus_client
    from prometheus_client import Counter, Histogram, Gauge, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not installed - metrics will not be collected")

# Define metrics - these will be initialized in init_metrics()
# HTTP request metrics
REQUEST_COUNT = None  # Counter for total requests
REQUEST_LATENCY = None  # Histogram for request duration

# Cache metrics
CACHE_HIT_COUNT = None  # Counter for cache hits
CACHE_MISS_COUNT = None  # Counter for cache misses
CACHE_SET_COUNT = None  # Counter for cache sets
CACHE_OP_LATENCY = None  # Histogram for cache operation duration

# Database metrics
DB_QUERY_COUNT = None  # Counter for database queries
DB_QUERY_LATENCY = None  # Histogram for query duration
DB_CONNECTION_ERRORS = None  # Counter for connection errors
DB_POOL_SIZE = None  # Gauge for connection pool size

# Task processing metrics
TASK_COUNT = None  # Counter for async tasks
TASK_LATENCY = None  # Histogram for task duration
TASK_SUCCESS = None  # Counter for successful tasks
TASK_FAILURE = None  # Counter for failed tasks

# Resource metrics
MEMORY_USAGE = None  # Gauge for memory usage
CPU_USAGE = None  # Gauge for CPU usage

# Metrics initialized flag
_metrics_initialized = False
_metrics_lock = threading.RLock()


def init_metrics() -> bool:
    """
    Initialize Prometheus metrics
    
    Returns:
        True if metrics were initialized successfully, False otherwise
    """
    global _metrics_initialized, REQUEST_COUNT, REQUEST_LATENCY
    global CACHE_HIT_COUNT, CACHE_MISS_COUNT, CACHE_SET_COUNT, CACHE_OP_LATENCY
    global DB_QUERY_COUNT, DB_QUERY_LATENCY, DB_CONNECTION_ERRORS, DB_POOL_SIZE
    global TASK_COUNT, TASK_LATENCY, TASK_SUCCESS, TASK_FAILURE
    global MEMORY_USAGE, CPU_USAGE
    
    # Use lock to prevent race conditions
    with _metrics_lock:
        # Return early if already initialized or Prometheus not available
        if _metrics_initialized or not PROMETHEUS_AVAILABLE:
            return _metrics_initialized
            
        try:
            # HTTP request metrics
            REQUEST_COUNT = Counter(
                'http_requests_total',
                'Total HTTP request count',
                ['method', 'endpoint', 'status']
            )
            
            REQUEST_LATENCY = Histogram(
                'http_request_duration_seconds',
                'HTTP request latency in seconds',
                ['method', 'endpoint']
            )
            
            # Cache metrics
            CACHE_HIT_COUNT = Counter(
                'cache_hits_total',
                'Total cache hit count',
                ['cache_type']
            )
            
            CACHE_MISS_COUNT = Counter(
                'cache_misses_total',
                'Total cache miss count',
                ['cache_type']
            )
            
            CACHE_SET_COUNT = Counter(
                'cache_sets_total',
                'Total cache set count',
                ['cache_type']
            )
            
            CACHE_OP_LATENCY = Histogram(
                'cache_operation_duration_seconds',
                'Cache operation latency in seconds',
                ['operation', 'cache_type']
            )
            
            # Database metrics
            DB_QUERY_COUNT = Counter(
                'db_queries_total',
                'Total database query count',
                ['operation', 'table']
            )
            
            DB_QUERY_LATENCY = Histogram(
                'db_query_duration_seconds',
                'Database query latency in seconds',
                ['operation', 'table']
            )
            
            DB_CONNECTION_ERRORS = Counter(
                'db_connection_errors_total',
                'Total database connection errors',
                ['error_type']
            )
            
            DB_POOL_SIZE = Gauge(
                'db_pool_size',
                'Database connection pool size',
                ['pool_type']
            )
            
            # Task processing metrics
            TASK_COUNT = Counter(
                'tasks_total',
                'Total async task count',
                ['task_name']
            )
            
            TASK_LATENCY = Histogram(
                'task_duration_seconds',
                'Task execution latency in seconds',
                ['task_name']
            )
            
            TASK_SUCCESS = Counter(
                'task_success_total',
                'Total successful task count',
                ['task_name']
            )
            
            TASK_FAILURE = Counter(
                'task_failure_total',
                'Total failed task count',
                ['task_name']
            )
            
            # Resource metrics
            MEMORY_USAGE = Gauge(
                'memory_usage_bytes',
                'Memory usage in bytes',
                ['type']
            )
            
            CPU_USAGE = Gauge(
                'cpu_usage_percent',
                'CPU usage percentage',
                ['type']
            )
            
            # Start resource metrics collection if in main process
            if os.environ.get('PROMETHEUS_MULTIPROC_DIR') is None:
                # Only do this in simple single-process deployments
                start_resource_metrics()
                
            # Mark as initialized
            _metrics_initialized = True
            logger.info("Prometheus metrics initialized")
            
            return True
            
        except Exception as e:
            logger.exception(f"Error initializing Prometheus metrics: {e}")
            return False
            

def get_metrics_handler():
    """
    Get Prometheus metrics handler for HTTP server
    
    Returns:
        Callable HTTP handler function or None if Prometheus not available
    """
    if not PROMETHEUS_AVAILABLE:
        return None
        
    # Initialize metrics if needed
    if not _metrics_initialized:
        init_metrics()
        
    # Return metrics handler
    return prometheus_client.make_wsgi_app()


def expose_metrics(port: int = 9090) -> bool:
    """
    Expose Prometheus metrics on a separate HTTP server
    
    Args:
        port: Port number to expose metrics on
        
    Returns:
        True if metrics server started successfully, False otherwise
    """
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not available, metrics server not started")
        return False
        
    # Initialize metrics if needed
    if not _metrics_initialized:
        init_metrics()
        
    try:
        # Start metrics server in a daemon thread
        prometheus_client.start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
        return True
        
    except Exception as e:
        logger.exception(f"Error starting Prometheus metrics server: {e}")
        return False


def track_request(method: str, endpoint: str, status: int, duration: float):
    """
    Track HTTP request metrics
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request endpoint (path)
        status: HTTP status code
        duration: Request duration in seconds
    """
    if not _metrics_initialized:
        return
        
    try:
        # Increment request counter
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        # Observe request latency
        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
    except Exception as e:
        logger.debug(f"Error tracking request metrics: {e}")


def track_cache_operation(cache_type: str, operation: str, duration: float):
    """
    Track cache operation metrics
    
    Args:
        cache_type: Type of cache (default, chart, etc.)
        operation: Cache operation (hit, miss, set)
        duration: Operation duration in seconds
    """
    if not _metrics_initialized:
        return
        
    try:
        # Track cache operation based on type
        if operation == "hit":
            CACHE_HIT_COUNT.labels(
                cache_type=cache_type
            ).inc()
        elif operation == "miss":
            CACHE_MISS_COUNT.labels(
                cache_type=cache_type
            ).inc()
        elif operation == "set":
            CACHE_SET_COUNT.labels(
                cache_type=cache_type
            ).inc()
            
        # Track operation latency
        CACHE_OP_LATENCY.labels(
            operation=operation,
            cache_type=cache_type
        ).observe(duration)
        
    except Exception as e:
        logger.debug(f"Error tracking cache metrics: {e}")


def track_db_query(operation: str, table: str, duration: float):
    """
    Track database query metrics
    
    Args:
        operation: Query operation (select, insert, update, delete)
        table: Database table name
        duration: Query duration in seconds
    """
    if not _metrics_initialized:
        return
        
    try:
        # Increment query counter
        DB_QUERY_COUNT.labels(
            operation=operation,
            table=table
        ).inc()
        
        # Observe query latency
        DB_QUERY_LATENCY.labels(
            operation=operation,
            table=table
        ).observe(duration)
        
    except Exception as e:
        logger.debug(f"Error tracking database metrics: {e}")


def track_db_error(error_type: str):
    """
    Track database error metrics
    
    Args:
        error_type: Type of error (connection, query, etc.)
    """
    if not _metrics_initialized:
        return
        
    try:
        # Increment error counter
        DB_CONNECTION_ERRORS.labels(
            error_type=error_type
        ).inc()
        
    except Exception as e:
        logger.debug(f"Error tracking database error metrics: {e}")


def track_task_start(task_name: str):
    """
    Track task start metrics
    
    Args:
        task_name: Name of the task
    """
    if not _metrics_initialized:
        return
        
    try:
        # Increment task counter
        TASK_COUNT.labels(
            task_name=task_name
        ).inc()
        
    except Exception as e:
        logger.debug(f"Error tracking task start metrics: {e}")


def track_task_complete(task_name: str, state: str):
    """
    Track task completion metrics
    
    Args:
        task_name: Name of the task
        state: Task state (SUCCESS, FAILURE, REVOKED, etc.)
    """
    if not _metrics_initialized:
        return
        
    try:
        # Track based on state
        if state == "SUCCESS":
            TASK_SUCCESS.labels(
                task_name=task_name
            ).inc()
        elif state == "FAILURE":
            TASK_FAILURE.labels(
                task_name=task_name
            ).inc()
            
    except Exception as e:
        logger.debug(f"Error tracking task completion metrics: {e}")


def track_task_success(task_name: str):
    """
    Track task success metrics
    
    Args:
        task_name: Name of the task
    """
    if not _metrics_initialized:
        return
        
    try:
        # Increment success counter
        TASK_SUCCESS.labels(
            task_name=task_name
        ).inc()
        
    except Exception as e:
        logger.debug(f"Error tracking task success metrics: {e}")


def track_task_failure(task_name: str, error: str):
    """
    Track task failure metrics
    
    Args:
        task_name: Name of the task
        error: Error message
    """
    if not _metrics_initialized:
        return
        
    try:
        # Increment failure counter
        TASK_FAILURE.labels(
            task_name=task_name
        ).inc()
        
    except Exception as e:
        logger.debug(f"Error tracking task failure metrics: {e}")


def start_resource_metrics(interval: float = 30.0):
    """
    Start collecting resource metrics in a background thread
    
    Args:
        interval: Collection interval in seconds
    """
    if not _metrics_initialized:
        return
        
    try:
        import psutil
        
        def collect_metrics():
            """Collect resource metrics"""
            while True:
                try:
                    # Get memory usage
                    memory = psutil.virtual_memory()
                    MEMORY_USAGE.labels(type="total").set(memory.total)
                    MEMORY_USAGE.labels(type="available").set(memory.available)
                    MEMORY_USAGE.labels(type="used").set(memory.used)
                    
                    # Get CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    CPU_USAGE.labels(type="system").set(cpu_percent)
                    
                    # Get process-specific metrics
                    process = psutil.Process(os.getpid())
                    process_cpu = process.cpu_percent(interval=1)
                    process_memory = process.memory_info().rss
                    
                    CPU_USAGE.labels(type="process").set(process_cpu)
                    MEMORY_USAGE.labels(type="process").set(process_memory)
                    
                except Exception as e:
                    logger.debug(f"Error collecting resource metrics: {e}")
                    
                # Sleep for the specified interval
                time.sleep(interval)
                
        # Start collection in a daemon thread
        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
        logger.info(f"Resource metrics collection started with interval {interval}s")
        
    except ImportError:
        logger.warning("psutil not installed, resource metrics disabled")
    except Exception as e:
        logger.exception(f"Error starting resource metrics collection: {e}")


# Initialize metrics if this module is imported
try:
    # Only auto-initialize in main process
    if os.environ.get('PROMETHEUS_MULTIPROC_DIR') is None:
        init_metrics()
except Exception as e:
    logger.debug(f"Error during metrics auto-initialization: {e}")