# Monitoring and Asynchronous Processing

This document explains the monitoring, observability, and asynchronous processing capabilities of the Natal Astrology Engine.

## Table of Contents

- [Monitoring and Observability](#monitoring-and-observability)
  - [Prometheus Metrics](#prometheus-metrics)
  - [Grafana Dashboards](#grafana-dashboards)
  - [Health Endpoints](#health-endpoints)
  - [Logging](#logging)
- [Asynchronous Processing](#asynchronous-processing)
  - [Celery Integration](#celery-integration)
  - [Async API Endpoints](#async-api-endpoints)
  - [Task Status Tracking](#task-status-tracking)
- [Redis Dual Purpose](#redis-dual-purpose)
  - [Cache Benefits](#cache-benefits)
  - [Broker Benefits](#broker-benefits)
- [Configuration Options](#configuration-options)

## Monitoring and Observability

The Natal Astrology Engine includes comprehensive monitoring and observability features to ensure reliable operation and performance insights.

### Prometheus Metrics

The system exposes Prometheus metrics at `/metrics` endpoint for both API and web components:

- **API Metrics**:
  - Request counts by endpoint
  - Request latency by endpoint
  - Error rates by endpoint and error type
  - Database operation counts and latency
  - Cache hit/miss ratios
  - API key usage tracking

- **Celery Task Metrics**:
  - Task counts by type
  - Task duration distributions
  - Task success/failure rates
  - Task queue lengths

- **System Metrics**:
  - Redis operations
  - Memory usage
  - CPU utilization

### Grafana Dashboards

Included Grafana dashboards provide visualization of all metrics:

1. **API Dashboard**: Overview of API performance, including request rates, latencies, and error rates.
2. **Redis Dashboard**: Cache and broker performance metrics for Redis.
3. **System Dashboard**: Overall system health and resource utilization.

Dashboards are automatically provisioned when using the provided Docker Compose setup.

### Health Endpoints

The `/api/health` endpoint provides a comprehensive health check of all system components:

```json
{
  "status": "healthy",
  "api": "healthy",
  "database": "healthy",
  "redis": "healthy",
  "celery": "healthy",
  "api_keys": {
    "status": "healthy",
    "count": 5
  },
  "version": "1.2.0",
  "uptime": "3d 5h 12m"
}
```

Health checks are also integrated with Docker health check mechanisms.

### Logging

The system uses structured logging with the following features:

- JSON-formatted logs for machine parsing
- Contextual information for all operations
- Request correlation IDs for tracing
- Error stack traces for debugging
- Configurable log levels via environment variables

## Asynchronous Processing

The Natal Astrology Engine supports asynchronous processing for computationally intensive operations, particularly AI-powered interpretations.

### Celery Integration

Celery is used for offloading heavy tasks:

- **Task Queue**: Redis serves as the broker for Celery tasks
- **Task Types**:
  - `generate_chart_interpretation`: Generates AI-powered natal chart interpretations
  - `generate_transit_interpretation`: Generates AI-powered transit interpretations
- **Fault Tolerance**: Tasks include automatic retries with exponential backoff
- **Scalability**: Worker count is configurable via environment variables

### Async API Endpoints

API endpoints that support asynchronous processing:

- `/api/interpret`: Natal chart interpretation
- `/api/interpret-transits`: Transit interpretation

Each endpoint accepts an `async_mode` parameter (boolean) that, when set to `true`, will process the request asynchronously and return a task ID.

Example async response:
```json
{
  "status": "processing",
  "task_id": "a3b2c1d0-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
  "message": "Chart interpretation is being generated asynchronously.",
  "check_result_endpoint": "/api/tasks/a3b2c1d0-e5f6-7g8h-9i0j-k1l2m3n4o5p6"
}
```

### Task Status Tracking

Clients can check task status with the `/api/tasks/{task_id}` endpoint:

- **Processing**: Task is still running
  ```json
  {
    "status": "processing",
    "task_id": "a3b2c1d0-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
    "state": "STARTED"
  }
  ```

- **Completed**: Task completed successfully
  ```json
  {
    "status": "completed",
    "task_id": "a3b2c1d0-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
    "result": "Full interpretation text..."
  }
  ```

- **Failed**: Task failed with an error
  ```json
  {
    "status": "failed",
    "task_id": "a3b2c1d0-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
    "error": "Error message..."
  }
  ```

## Redis Dual Purpose

Redis serves a dual purpose in this architecture:

### Cache Benefits

- Caches expensive chart calculations
- Improves API response times
- Reduces computational load
- Efficient memory usage with TTL-based expiration

### Broker Benefits

- Reliable message queue for Celery tasks
- Low latency task dispatching
- Persistence for task results
- Built-in monitoring capabilities

## Configuration Options

The system can be configured via environment variables:

- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379/0`)
- `REDIS_CACHE_TTL`: Cache TTL in seconds (default: `3600`)
- `CELERY_WORKERS`: Number of Celery worker processes (default: `2`)
- `CELERY_TASK_TIMEOUT`: Task timeout in seconds (default: `600`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `PROMETHEUS_ENABLED`: Enable Prometheus metrics (default: `true`)
- `SENTRY_DSN`: Sentry DSN for error tracking (optional)

For more configuration options, see the Docker Compose file and environment variable documentation.