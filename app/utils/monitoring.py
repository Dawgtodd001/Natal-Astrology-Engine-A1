"""
Monitoring utilities for the Natal Astrology Engine
Includes Prometheus metrics and Sentry integration
"""
import os
import time
from typing import Callable, Dict, Any, Optional
import sentry_sdk
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import multiprocess, CollectorRegistry
from fastapi import FastAPI, Request, Response
from sqlalchemy.exc import OperationalError
from app.utils.logging import get_logger
from app.database import SessionLocal

logger = get_logger(__name__)

# Initialize metrics
REQUEST_COUNT = Counter(
    'natal_api_requests_total', 
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'natal_api_request_latency_seconds', 
    'Request latency in seconds',
    ['method', 'endpoint']
)

CHART_CALCULATION_COUNT = Counter(
    'natal_chart_calculations_total', 
    'Total number of chart calculations',
    ['house_system', 'zodiac_type', 'cached']
)

CHART_CALCULATION_LATENCY = Histogram(
    'natal_chart_calculation_latency_seconds', 
    'Chart calculation latency in seconds',
    ['house_system', 'zodiac_type', 'cached']
)

REDIS_AVAILABLE = Gauge(
    'natal_redis_available', 
    'Redis cache availability (1=available, 0=unavailable)'
)

DATABASE_AVAILABLE = Gauge(
    'natal_database_available', 
    'Database availability (1=available, 0=unavailable)'
)

API_KEYS_ACTIVE = Gauge(
    'natal_api_keys_active', 
    'Number of active API keys'
)

def init_sentry(app: FastAPI) -> None:
    """Initialize Sentry integration if DSN is provided"""
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        logger.info("Initializing Sentry integration")
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,
            profiles_sample_rate=0.5,
            enable_tracing=True,
            environment=os.environ.get("ENVIRONMENT", "development"),
            release=os.environ.get("APP_VERSION", "1.0.0"),
        )
        
        @app.middleware("http")
        async def sentry_exception_middleware(request: Request, call_next):
            """Middleware to capture exceptions in Sentry"""
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                # This is where it will be caught and sent to Sentry
                sentry_sdk.capture_exception(e)
                # Re-raise to let FastAPI handle it
                raise
    else:
        logger.warning("Sentry DSN not provided, skipping Sentry integration")

def check_database_health() -> Dict[str, Any]:
    """Check database health and return status"""
    try:
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        DATABASE_AVAILABLE.set(1)
        return {"database": "UP"}
    except OperationalError as e:
        DATABASE_AVAILABLE.set(0)
        return {"database": "DOWN", "error": str(e)}
    except Exception as e:
        DATABASE_AVAILABLE.set(0)
        return {"database": "DOWN", "error": str(e)}

def prometheus_middleware(app: FastAPI) -> None:
    """Add Prometheus middleware to FastAPI app"""
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        """Middleware to collect request metrics"""
        start_time = time.time()
        response = await call_next(request)
        
        # Skip metrics endpoint to avoid recursion
        if request.url.path != "/metrics":
            process_time = time.time() - start_time
            
            # Record request count and latency
            endpoint = request.url.path
            REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
            REQUEST_LATENCY.labels(request.method, endpoint).observe(process_time)
        
        return response

    @app.get("/metrics")
    def metrics():
        """Endpoint to expose Prometheus metrics"""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

def setup_health_endpoint(app: FastAPI) -> None:
    """Add health check endpoint to FastAPI app"""
    from app.utils.redis_cache import is_redis_available
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint for the API"""
        # Check database health
        db_status = check_database_health()
        
        # Check Redis health
        redis_available = is_redis_available()
        REDIS_AVAILABLE.set(1 if redis_available else 0)
        redis_status = {"redis": "UP"} if redis_available else {"redis": "DOWN"}
        
        # Combine status
        service_status = "UP" if db_status.get("database") == "UP" and redis_status.get("redis") == "UP" else "DOWN"
        
        return {
            "status": service_status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "services": {
                **db_status,
                **redis_status
            }
        }

def setup_error_endpoint(app: FastAPI) -> None:
    """Add test error endpoint for Sentry"""
    @app.get("/debug/error")
    async def test_error():
        """Test endpoint to trigger a Sentry error"""
        sentry_dsn = os.environ.get("SENTRY_DSN")
        if not sentry_dsn:
            return {"message": "Sentry not configured. Set SENTRY_DSN to test error reporting."}
            
        # Intentionally raise an exception to test Sentry
        try:
            division_by_zero = 1 / 0
            return {"message": "This should never be returned"}
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return {"message": "Error captured and sent to Sentry", "error": str(e)}

def init_monitoring(app: FastAPI) -> None:
    """Initialize all monitoring components"""
    # Initialize Sentry
    init_sentry(app)
    
    # Add Prometheus middleware
    prometheus_middleware(app)
    
    # Set up health and error endpoints
    setup_health_endpoint(app)
    setup_error_endpoint(app)
    
    logger.info("Monitoring system initialized with Prometheus metrics and health endpoints")