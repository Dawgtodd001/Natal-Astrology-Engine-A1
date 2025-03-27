"""
Main FastAPI application for the API Gateway service

This module provides the main FastAPI application for the API Gateway service.
"""

import logging
import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Optional, List, Callable

# Prometheus metrics
import prometheus_client

# FastAPI imports
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import RedirectResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

# Import API router
from api_gateway.app.api.api_v1.api import api_router

# Import middleware
from api_gateway.app.middleware.correlation import CorrelationMiddleware
from api_gateway.app.middleware.metrics import PrometheusMiddleware
from api_gateway.app.middleware.logging import LoggingMiddleware
from api_gateway.app.middleware.auth import APIKeyMiddleware
from api_gateway.app.middleware.rate_limit import RateLimitMiddleware

# Import settings
from api_gateway.app.core.settings import settings

# Import database utilities
from api_gateway.app.db.session import close_db_connections
from api_gateway.app.db.init_db import init_db

# Get logger
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    # Create FastAPI app with custom settings
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url=None,  # Disable default docs
        redoc_url=None,  # Disable default redoc
        openapi_url=settings.OPENAPI_URL if settings.APP_ENV != "production" else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # Add correlation ID middleware
    app.add_middleware(CorrelationMiddleware)
    
    # Add Prometheus metrics middleware
    if settings.ENABLE_METRICS:
        app.add_middleware(PrometheusMiddleware)
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Add API Key middleware
    app.add_middleware(APIKeyMiddleware)
    
    # Add rate limiting middleware
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Add exception handlers
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Add custom endpoints
    add_custom_endpoints(app)
    
    # Add event handlers
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)
    
    # Log app initialization
    logger.info(f"API Gateway {settings.APP_VERSION} initialized in {settings.APP_ENV} mode")
    
    return app


def add_custom_endpoints(app: FastAPI) -> None:
    """
    Add custom endpoints to the application
    
    Args:
        app: FastAPI application
    """
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs" if settings.APP_ENV != "production" else "/api/v1")
    
    # Custom Swagger UI endpoint
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=settings.OPENAPI_URL,
            title=f"{settings.APP_NAME} - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        )
    
    # Metrics endpoint
    if settings.ENABLE_METRICS:
        @app.get("/metrics", include_in_schema=False)
        async def metrics():
            return Response(content=prometheus_client.generate_latest(), media_type="text/plain")


async def startup_event() -> None:
    """
    Startup event handler
    
    This function is called when the application starts up
    """
    try:
        # Initialize database
        init_db()
        
        # Log startup
        logger.info("API Gateway service started")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        traceback.print_exc()
        sys.exit(1)


async def shutdown_event() -> None:
    """
    Shutdown event handler
    
    This function is called when the application shuts down
    """
    try:
        # Close database connections
        close_db_connections()
        
        # Log shutdown
        logger.info("API Gateway service stopped")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler
    
    This function handles all unhandled exceptions
    
    Args:
        request: FastAPI request
        exc: Exception
        
    Returns:
        JSONResponse: Error response
    """
    # Log exception
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    
    # Return error response
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": f"Internal server error: {str(exc)}",
            "correlation_id": request.state.correlation_id if hasattr(request.state, "correlation_id") else None,
            "timestamp": time.time(),
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    HTTP exception handler
    
    This function handles HTTP exceptions
    
    Args:
        request: FastAPI request
        exc: HTTP exception
        
    Returns:
        JSONResponse: Error response
    """
    # Extract headers
    headers = getattr(exc, "headers", None)
    
    # Create error response
    error_response = {
        "status": "error",
        "message": str(exc.detail),
        "code": exc.status_code,
        "correlation_id": request.state.correlation_id if hasattr(request.state, "correlation_id") else None,
        "timestamp": time.time(),
    }
    
    # Log exception based on status code
    if exc.status_code >= 500:
        logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    elif exc.status_code >= 400:
        logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    
    # Return error response
    return JSONResponse(
        content=error_response,
        status_code=exc.status_code,
        headers=headers,
    )


# Create FastAPI application
app = create_app()


# Run development server if executed directly
if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": settings.LOG_FORMAT,
            },
        },
        "handlers": {
            "default": {
                "level": settings.LOG_LEVEL,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": settings.LOG_LEVEL,
                "propagate": True
            },
            "uvicorn": {
                "handlers": ["default"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
        },
    }
    
    # Run server
    uvicorn.run(
        "api_gateway.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        log_config=logging_config,
    )