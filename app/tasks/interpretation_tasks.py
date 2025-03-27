"""
Celery tasks for AI-powered chart interpretations
"""
import time
import logging
from typing import Dict, Any, List, Optional

from prometheus_client import Counter, Summary
from celery.signals import task_prerun, task_postrun

from ..celery_app import celery_app

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics for task monitoring
TASK_RUNS = Counter(
    'natal_celery_task_runs_total',
    'Number of Celery task runs',
    ['task_name', 'status']
)

TASK_RUNTIME = Summary(
    'natal_celery_task_runtime_seconds',
    'Time spent processing tasks',
    ['task_name']
)

# Record task start time for metrics
@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, *args, **kwargs):
    logger.info(f"Starting task {task.name} [{task_id}]")
    task.start_time = time.time()
    TASK_RUNS.labels(task_name=task.name, status='started').inc()

# Record task completion time and metrics
@task_postrun.connect
def task_postrun_handler(task_id=None, task=None, state=None, *args, **kwargs):
    runtime = time.time() - getattr(task, 'start_time', time.time())
    logger.info(f"Task {task.name} [{task_id}] completed with status {state} in {runtime:.2f}s")
    TASK_RUNTIME.labels(task_name=task.name).observe(runtime)
    TASK_RUNS.labels(task_name=task.name, status=state.lower()).inc()

@celery_app.task(
    bind=True,
    name='app.tasks.interpretation_tasks.generate_chart_interpretation',
    max_retries=2,
    default_retry_delay=30
)
def generate_chart_interpretation(
    self,
    chart_data: Dict[str, Any],
    birth_info: Dict[str, Any],
    style: Optional[str] = "detailed"
) -> str:
    """
    Generate an AI-powered interpretation of the birth chart (async task)
    
    Args:
        chart_data: Complete chart data dictionary
        birth_info: Birth information dictionary
        style: Style of interpretation ("concise", "detailed", "spiritual", "psychological")
        
    Returns:
        Rendered interpretation text
    """
    try:
        # Import here to avoid circular imports
        from ..ai.openai_integration import generate_chart_interpretation as _generate
        
        # Add a small delay to simulate AI processing time (if not in production)
        # This helps for testing the async nature of the task
        if self.request.retries == 0:
            logger.info(f"Generating chart interpretation in style: {style}")
        
        # Generate the interpretation
        interpretation = _generate(chart_data, birth_info, style)
        return interpretation
        
    except Exception as e:
        logger.error(f"Error generating chart interpretation: {str(e)}")
        # Retry the task with exponential backoff
        retry_countdown = 30 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=retry_countdown)

@celery_app.task(
    bind=True,
    name='app.tasks.interpretation_tasks.generate_transit_interpretation',
    max_retries=2,
    default_retry_delay=30
)
def generate_transit_interpretation(
    self,
    natal_chart: Dict[str, Any],
    transit_chart: Dict[str, Any],
    transit_aspects: List[Dict[str, Any]],
    birth_info: Dict[str, Any],
    transit_info: Dict[str, Any],
    style: Optional[str] = "detailed"
) -> str:
    """
    Generate an AI-powered interpretation of transit aspects to a natal chart (async task)
    
    Args:
        natal_chart: Natal chart data dictionary
        transit_chart: Transit chart data dictionary
        transit_aspects: List of transit-to-natal aspect dictionaries
        birth_info: Birth information dictionary
        transit_info: Transit date information dictionary
        style: Style of interpretation ("concise", "detailed", "predictive", "growth")
        
    Returns:
        Rendered interpretation text
    """
    try:
        # Import here to avoid circular imports
        from ..ai.openai_integration import generate_transit_interpretation as _generate
        
        # Add a small delay to simulate AI processing time (if not in production)
        # This helps for testing the async nature of the task
        if self.request.retries == 0:
            logger.info(f"Generating transit interpretation in style: {style}")
        
        # Generate the interpretation
        interpretation = _generate(
            natal_chart, 
            transit_chart, 
            transit_aspects, 
            birth_info, 
            transit_info, 
            style
        )
        return interpretation
        
    except Exception as e:
        logger.error(f"Error generating transit interpretation: {str(e)}")
        # Retry the task with exponential backoff
        retry_countdown = 30 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=retry_countdown)