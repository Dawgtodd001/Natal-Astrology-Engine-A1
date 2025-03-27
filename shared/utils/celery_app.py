"""
Celery application setup for the Natal Astrology Engine microservices
"""
import os
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable

# Load environment settings
from shared.config.settings import settings

# Set up logging
logger = logging.getLogger(__name__)

# Try to import Celery with fallback
try:
    from celery import Celery
    from celery.app import trace
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery package not installed - async task processing will not be available")


def create_celery_app(app_name: str = None) -> Any:
    """
    Create a Celery application instance with proper configuration
    
    Args:
        app_name: Name of the app for Celery task namespace
    
    Returns:
        Celery application instance or None if Celery is not available
    """
    if not CELERY_AVAILABLE:
        logger.warning("Celery not available, returning dummy app")
        return DummyCeleryApp()
    
    # Use the provided app name or get from settings
    app_name = app_name or settings.APP_NAME.lower().replace(" ", "_")
    
    # Create Celery app
    app = Celery(
        app_name,
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    
    # Configure Celery
    app.conf.update(
        # Task settings
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        
        # Result settings
        result_expires=60 * 60 * 24,  # 24 hours
        
        # Performance settings
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        
        # Retry settings
        task_publish_retry=True,
        task_publish_retry_policy={
            "max_retries": 3,
            "interval_start": 0.2,
            "interval_step": 0.5,
            "interval_max": 1.0,
        },
        
        # Logging
        worker_redirect_stdouts=False,
        worker_log_format=settings.LOG_FORMAT,
    )
    
    # Set Redis visibility timeout
    app.conf.broker_transport_options = {
        "visibility_timeout": int(settings.CELERY_TASK_TIMEOUT),
    }
    
    # Set up task tracking
    setup_task_monitoring(app)
    
    return app


def setup_task_monitoring(app):
    """Set up Celery task monitoring with Prometheus metrics"""
    if not CELERY_AVAILABLE:
        return

    try:
        # Import Celery signals
        from celery.signals import (
            task_prerun, task_postrun, task_success,
            task_failure, task_retry, worker_ready
        )
        
        # Prometheus metrics are imported here to avoid circular imports
        from shared.monitoring.metrics import (
            track_task_start, track_task_complete, 
            track_task_success, track_task_failure
        )
        
        # Set up signal handlers for task metrics
        @task_prerun.connect
        def task_prerun_handler(task_id=None, task=None, *args, **kwargs):
            """Handle task start event"""
            try:
                track_task_start(task.name)
            except Exception as e:
                logger.exception(f"Error tracking task start: {e}")
                
        @task_postrun.connect
        def task_postrun_handler(task_id=None, task=None, state=None, *args, **kwargs):
            """Handle task completion event"""
            try:
                track_task_complete(task.name, state)
            except Exception as e:
                logger.exception(f"Error tracking task completion: {e}")
                
        @task_success.connect
        def task_success_handler(sender=None, result=None, *args, **kwargs):
            """Handle task success event"""
            try:
                if sender:
                    track_task_success(sender.name)
            except Exception as e:
                logger.exception(f"Error tracking task success: {e}")
                
        @task_failure.connect
        def task_failure_handler(sender=None, exception=None, *args, **kwargs):
            """Handle task failure event"""
            try:
                if sender:
                    track_task_failure(sender.name, str(exception))
            except Exception as e:
                logger.exception(f"Error tracking task failure: {e}")
                
        @worker_ready.connect
        def worker_ready_handler(*args, **kwargs):
            """Handle worker ready event"""
            logger.info("Celery worker is ready")
            
    except ImportError:
        logger.warning("Prometheus client not available, task monitoring disabled")
    except Exception as e:
        logger.exception(f"Error setting up task monitoring: {e}")


class DummyCeleryApp:
    """
    Dummy Celery app implementation for when Celery is not available
    
    This provides a minimal API-compatible interface to avoid errors
    when Celery is not installed but code tries to use it.
    """
    def __init__(self):
        self.conf = type('DummyConf', (), {
            'update': lambda *args, **kwargs: None,
            'broker_transport_options': {},
        })
        self.tasks = {}
        
    def task(self, *args, **kwargs):
        """Dummy task decorator that just returns the original function"""
        def decorator(func):
            self.tasks[func.__name__] = func
            func.delay = lambda *args, **kwargs: DummyAsyncResult(
                task_id="dummy",
                status="FAILURE",
                result=Exception("Celery not available"),
                traceback=None
            )
            func.apply_async = lambda *args, **kwargs: func.delay()
            return func
        
        # Handle both @app.task and @app.task()
        if len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        return decorator
    
    def send_task(self, *args, **kwargs):
        """Dummy send_task implementation"""
        return DummyAsyncResult(
            task_id="dummy",
            status="FAILURE",
            result=Exception("Celery not available"),
            traceback=None
        )


class DummyAsyncResult:
    """Dummy AsyncResult implementation for the DummyCeleryApp"""
    def __init__(self, task_id, status, result, traceback):
        self.task_id = task_id
        self.status = status
        self._result = result
        self._traceback = traceback
        
    def get(self, timeout=None, propagate=True, **kwargs):
        """Get the task result"""
        if propagate and isinstance(self._result, Exception):
            raise self._result
        return self._result
        
    def ready(self):
        """Check if the task is ready"""
        return True
        
    @property
    def result(self):
        """Get the task result"""
        return self._result
        
    @property
    def traceback(self):
        """Get the task traceback"""
        return self._traceback


# Create global Celery app instance
celery_app = create_celery_app()

# Export for imports
__all__ = ["celery_app", "create_celery_app"]