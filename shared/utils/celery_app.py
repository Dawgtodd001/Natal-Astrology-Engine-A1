"""
Celery configuration for the Natal Astrology Engine microservices.

This module provides a shared Celery configuration that can be
imported and used by any microservice that needs to perform
asynchronous task processing.
"""

import os
import logging
import datetime
from typing import Dict, Any, Optional

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

# Set up logger
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_RESULT_TTL = 3600  # 1 hour
DEFAULT_TASK_SOFT_TIMEOUT = 600  # 10 minutes
DEFAULT_TASK_HARD_TIMEOUT = 1200  # 20 minutes
DEFAULT_TASK_SERIALIZER = "json"
DEFAULT_RESULT_SERIALIZER = "json"
DEFAULT_ACCEPT_CONTENT = ["json"]
DEFAULT_TIMEZONE = "UTC"
DEFAULT_REDIS_MAX_CONNECTIONS = 10


def create_celery_app(service_name: str) -> Optional['Celery']:
    """
    Create and configure a Celery application for a specific service.
    
    Args:
        service_name: Name of the service using this Celery instance
        
    Returns:
        Configured Celery application or None if Celery is not available
    """
    if not CELERY_AVAILABLE:
        logger.warning("Celery package is not installed")
        return None
    
    # Get Redis URL from environment or use default
    redis_url = os.environ.get("REDIS_URL", DEFAULT_REDIS_URL)
    
    # Create Celery app
    app = Celery(
        service_name,
        broker=redis_url,
        backend=redis_url
    )
    
    # Configure Celery
    app.conf.update(
        # Task result settings
        result_backend=redis_url,
        result_expires=int(os.environ.get("CELERY_RESULT_TTL", DEFAULT_RESULT_TTL)),
        
        # Serialization
        task_serializer=DEFAULT_TASK_SERIALIZER,
        result_serializer=DEFAULT_RESULT_SERIALIZER,
        accept_content=DEFAULT_ACCEPT_CONTENT,
        
        # Task execution settings
        task_soft_time_limit=int(os.environ.get("CELERY_TASK_SOFT_TIMEOUT", DEFAULT_TASK_SOFT_TIMEOUT)),
        task_time_limit=int(os.environ.get("CELERY_TASK_HARD_TIMEOUT", DEFAULT_TASK_HARD_TIMEOUT)),
        
        # Worker settings
        worker_prefetch_multiplier=1,  # Fetch one task at a time
        worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
        worker_concurrency=int(os.environ.get("CELERY_WORKERS", 2)),
        
        # Beat settings (if scheduled tasks are needed)
        beat_schedule={},
        
        # Timezone
        timezone=DEFAULT_TIMEZONE,
        enable_utc=True,
        
        # Broker settings
        broker_transport_options={
            'visibility_timeout': 3600,  # 1 hour - adjust based on longest task
            'max_connections': int(os.environ.get("REDIS_MAX_CONNECTIONS", DEFAULT_REDIS_MAX_CONNECTIONS)),
        },
        
        # Logging
        worker_hijack_root_logger=False,
        
        # Task routes (customize based on service needs)
        task_routes={}
    )
    
    # Set up task routes based on service
    if service_name == "interpretation":
        app.conf.task_routes = {
            'app.tasks.interpretation_tasks.*': {'queue': 'interpretation'},
        }
    elif service_name == "chart_calculation":
        app.conf.task_routes = {
            'app.tasks.calculation_tasks.*': {'queue': 'calculation'},
        }
    
    return app


# Define task monitoring signals if Celery is available
if CELERY_AVAILABLE:
    from celery.signals import (
        task_prerun,
        task_postrun,
        task_success,
        task_failure,
        task_retry,
    )
    
    @task_prerun.connect
    def task_prerun_handler(task_id, task, args, kwargs, **extra):
        """Log when a task starts running"""
        logger.info(f"Task started: {task.name}[{task_id}]")
        
        # Add start time to task request for duration calculation
        task.request.start_time = datetime.datetime.now()
        
        # Import here to avoid circular imports
        try:
            from shared.monitoring.prometheus import track_task_execution
            track_task_execution(
                task_type=task.name.split('.')[-1],
                status="started",
                service=task.name.split('.')[0]
            )
        except ImportError:
            pass
    
    @task_success.connect
    def task_success_handler(result, **kwargs):
        """Log when a task completes successfully"""
        sender = kwargs.get('sender')
        if not sender:
            return
        
        task_id = sender.request.id
        task_name = sender.name
        
        # Calculate task duration
        start_time = getattr(sender.request, 'start_time', None)
        elapsed_time = None
        if start_time:
            elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
            logger.info(f"Task succeeded: {task_name}[{task_id}] in {elapsed_time:.2f}s")
        else:
            logger.info(f"Task succeeded: {task_name}[{task_id}]")
        
        # Import here to avoid circular imports
        try:
            from shared.monitoring.prometheus import track_task_execution
            track_task_execution(
                task_type=task_name.split('.')[-1],
                status="success",
                service=task_name.split('.')[0],
                elapsed_time=elapsed_time
            )
        except ImportError:
            pass
    
    @task_failure.connect
    def task_failure_handler(sender, task_id, exception, args, kwargs, **extra):
        """Log when a task fails"""
        # Calculate task duration
        start_time = getattr(sender.request, 'start_time', None)
        elapsed_time = None
        if start_time:
            elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
            logger.error(f"Task failed: {sender.name}[{task_id}] in {elapsed_time:.2f}s: {exception}")
        else:
            logger.error(f"Task failed: {sender.name}[{task_id}]: {exception}")
        
        # Import here to avoid circular imports
        try:
            from shared.monitoring.prometheus import track_task_execution
            track_task_execution(
                task_type=sender.name.split('.')[-1],
                status="failure",
                service=sender.name.split('.')[0],
                elapsed_time=elapsed_time
            )
        except ImportError:
            pass
    
    @task_retry.connect
    def task_retry_handler(sender, request, reason, einfo, **kwargs):
        """Log when a task is retried"""
        logger.warning(f"Task retrying: {sender.name}[{request.id}]. Reason: {reason}")
        
        # Import here to avoid circular imports
        try:
            from shared.monitoring.prometheus import track_task_execution
            track_task_execution(
                task_type=sender.name.split('.')[-1],
                status="retry",
                service=sender.name.split('.')[0]
            )
        except ImportError:
            pass