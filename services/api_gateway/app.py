"""
API Gateway service for the Natal Astrology Engine

This service acts as the central entry point for all API requests
"""
import os
import logging
from typing import List, Dict, Any, Optional, Callable

# Import FastAPI
try:
    from fastapi import FastAPI, Request, Response, Depends, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import HTMLResponse, StreamingResponse
    from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    
# Import settings from shared config
from shared.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class NotAvailableError(Exception):
    """Error raised when FastAPI is not available"""
    pass


def create_app() -> Any:
    """
    Create and configure FastAPI application
    
    Returns:
        FastAPI application instance
    
    Raises:
        NotAvailableError: If FastAPI is not available
    """
    if not FASTAPI_AVAILABLE:
        logger.error("FastAPI not available. Install it with 'pip install fastapi'")
        raise NotAvailableError("FastAPI is not available")
    
    # Create FastAPI application
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url=None,  # We'll customize the docs URL
        redoc_url=None,  # We'll customize the redoc URL
        openapi_url="/api/openapi.json"
    )
    
    # Add startup event handler
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler"""
        logger.info(f"Starting {settings.APP_NAME} API Gateway service")
        
        # Initialize Prometheus metrics
        from shared.monitoring.metrics import init_metrics, expose_metrics
        init_metrics()
        
        # Start metrics server if enabled
        if settings.ENABLE_METRICS:
            expose_metrics(settings.METRICS_PORT)
    
    # Add shutdown event handler
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler"""
        logger.info(f"Shutting down {settings.APP_NAME} API Gateway service")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        allow_credentials=True,
    )
    
    # Add correlation ID middleware
    from services.api_gateway.middleware.correlation import CorrelationIdMiddleware
    app.add_middleware(CorrelationIdMiddleware)
    
    # Add metrics middleware
    from services.api_gateway.middleware.metrics import PrometheusMiddleware
    app.add_middleware(PrometheusMiddleware)
    
    # Add rate limiting middleware if enabled
    if settings.RATE_LIMIT_ENABLED:
        # Check if rate_limit module exists first
        try:
            from services.api_gateway.middleware.rate_limit import RateLimitMiddleware
            app.add_middleware(RateLimitMiddleware)
        except ImportError:
            logger.warning("Rate limit middleware not available, skipping")
    
    # Add authentication middleware
    from services.api_gateway.middleware.auth import AuthenticationMiddleware
    app.add_middleware(AuthenticationMiddleware)
    
    # Add logging middleware (after correlation ID middleware)
    from services.api_gateway.middleware.logging import LoggingMiddleware
    app.add_middleware(LoggingMiddleware)
    
    # Add global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global exception handler for unhandled exceptions
        
        This captures all uncaught exceptions and returns a consistent response
        """
        logger.exception(f"Uncaught exception: {str(exc)}")
        
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error occurred"}
        )
    
    # Add custom docs routes
    @app.get("/api/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Custom Swagger UI route with authentication"""
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - API Documentation",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )
    
    @app.get("/api/redoc", include_in_schema=False)
    async def custom_redoc_html():
        """Custom ReDoc route with authentication"""
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - API Documentation",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        )
    
    # Root API route
    @app.get("/api", include_in_schema=False)
    async def api_root():
        """Root API endpoint with service information"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": settings.APP_DESCRIPTION,
            "docs_url": f"/api/docs",
            "redoc_url": f"/api/redoc"
        }
    
    # Include API routes with versioning
    try:
        from services.api_gateway.api.v1 import router as api_v1_router
        app.include_router(api_v1_router, prefix="/api")
    except ImportError:
        logger.warning("API v1 router not found, skipping API routes inclusion")
        # Add a basic health endpoint since the router is missing
        @app.get("/api/health")
        async def health_check():
            return {"status": "ok", "api": "running"}
    
    return app