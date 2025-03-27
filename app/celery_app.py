"""
Celery configuration for the Natal Astrology Engine
"""
import os
import redis
from celery import Celery

# Get Redis URL from environment or use default
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Create Redis client for use in health checks and other operations
redis_client = redis.from_url(redis_url)

# Create Celery instance
celery_app = Celery(
    'natal_astrology',
    broker=redis_url,
    backend=redis_url,
    include=['app.tasks.interpretation_tasks']
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    worker_prefetch_multiplier=1,  # Process tasks one at a time
    worker_concurrency=2,  # Number of worker processes
)

# Set Redis visibility timeout to match task time limit
celery_app.conf.broker_transport_options = {
    'visibility_timeout': 3600,  # 1 hour
}

# Add Prometheus metrics for Celery tasks
celery_app.conf.task_routes = {
    'app.tasks.interpretation_tasks.*': {'queue': 'interpretation'},
}

if __name__ == '__main__':
    celery_app.start()