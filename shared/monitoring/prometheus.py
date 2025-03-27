"""
Prometheus metrics utilities for microservices.

This module provides common Prometheus metrics functionality
that can be used across all microservices.
"""

import time
from typing import Callable, Dict, List, Optional

try:
    import prometheus_client
    from prometheus_client import Counter, Gauge, Histogram, multiprocess
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Define common metrics that can be used across services
if PROMETHEUS_AVAILABLE:
    # API metrics
    REQUEST_COUNT = Counter(
        'http_requests_total',
        'Total number of HTTP requests',
        ['method', 'endpoint', 'status_code', 'service']
    )
    
    REQUEST_LATENCY = Histogram(
        'http_request_duration_seconds',
        'HTTP request latency in seconds',
        ['method', 'endpoint', 'service'],
        buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0)
    )
    
    # Cache metrics
    CACHE_HIT_COUNT = Counter(
        'cache_hit_total',
        'Total number of cache hits',
        ['cache_type', 'service']
    )
    
    CACHE_MISS_COUNT = Counter(
        'cache_miss_total',
        'Total number of cache misses',
        ['cache_type', 'service']
    )
    
    # Database metrics
    DB_QUERY_COUNT = Counter(
        'db_query_total',
        'Total number of database queries',
        ['operation', 'table', 'service']
    )
    
    DB_QUERY_LATENCY = Histogram(
        'db_query_duration_seconds',
        'Database query latency in seconds',
        ['operation', 'table', 'service'],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
    )
    
    # Resource metrics
    MEMORY_USAGE = Gauge(
        'memory_usage_bytes',
        'Memory usage in bytes',
        ['service']
    )

    # Task metrics
    TASK_COUNT = Counter(
        'task_total',
        'Total number of tasks',
        ['task_type', 'status', 'service'] 
    )
    
    TASK_LATENCY = Histogram(
        'task_duration_seconds',
        'Task execution latency in seconds',
        ['task_type', 'service'],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
    )


def setup_prometheus_multiproc() -> None:
    """
    Set up Prometheus for multiprocess mode.
    
    This function must be called when using gunicorn or uvicorn with multiple workers.
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    try:
        prometheus_client.multiprocess.MultiProcessCollector(prometheus_client.REGISTRY)
    except Exception as e:
        print(f"Failed to set up Prometheus multiprocess mode: {e}")


def generate_metrics() -> str:
    """
    Generate Prometheus metrics output.
    
    Returns:
        str: Prometheus metrics in text format
    """
    if not PROMETHEUS_AVAILABLE:
        return "# Prometheus metrics not available"
    
    return prometheus_client.generate_latest().decode('utf-8')


def track_request_latency(
    method: str,
    endpoint: str,
    service: str,
    status_code: int,
    elapsed_time: float
) -> None:
    """
    Track HTTP request latency and count.
    
    Args:
        method: HTTP method
        endpoint: API endpoint path
        service: Service name
        status_code: HTTP status code
        elapsed_time: Request processing time in seconds
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        service=service
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=method,
        endpoint=endpoint,
        service=service
    ).observe(elapsed_time)


def track_cache_operation(
    cache_type: str,
    hit: bool,
    service: str
) -> None:
    """
    Track cache hit/miss operations.
    
    Args:
        cache_type: Type of cache (e.g., 'chart', 'interpretation')
        hit: True if cache hit, False if cache miss
        service: Service name
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    if hit:
        CACHE_HIT_COUNT.labels(
            cache_type=cache_type,
            service=service
        ).inc()
    else:
        CACHE_MISS_COUNT.labels(
            cache_type=cache_type,
            service=service
        ).inc()


def track_db_operation(
    operation: str,
    table: str,
    service: str,
    elapsed_time: float
) -> None:
    """
    Track database operation count and latency.
    
    Args:
        operation: Database operation type (e.g., 'select', 'insert')
        table: Database table name
        service: Service name
        elapsed_time: Operation time in seconds
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    DB_QUERY_COUNT.labels(
        operation=operation,
        table=table,
        service=service
    ).inc()
    
    DB_QUERY_LATENCY.labels(
        operation=operation,
        table=table,
        service=service
    ).observe(elapsed_time)


def track_task_execution(
    task_type: str,
    status: str,
    service: str,
    elapsed_time: Optional[float] = None
) -> None:
    """
    Track task execution count and latency.
    
    Args:
        task_type: Type of task (e.g., 'chart_interpretation')
        status: Task status ('success', 'failure', 'started')
        service: Service name
        elapsed_time: Task execution time in seconds (optional)
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    TASK_COUNT.labels(
        task_type=task_type,
        status=status,
        service=service
    ).inc()
    
    if elapsed_time is not None and status in ('success', 'failure'):
        TASK_LATENCY.labels(
            task_type=task_type,
            service=service
        ).observe(elapsed_time)


def update_memory_usage(service: str, usage_bytes: int) -> None:
    """
    Update memory usage gauge.
    
    Args:
        service: Service name
        usage_bytes: Memory usage in bytes
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    MEMORY_USAGE.labels(service=service).set(usage_bytes)


def timing_decorator(operation: str, table: str, service: str) -> Callable:
    """
    Decorator to time database operations and record metrics.
    
    Args:
        operation: Database operation type
        table: Database table name
        service: Service name
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            
            track_db_operation(
                operation=operation,
                table=table,
                service=service,
                elapsed_time=elapsed_time
            )
            
            return result
        return wrapper
    return decorator