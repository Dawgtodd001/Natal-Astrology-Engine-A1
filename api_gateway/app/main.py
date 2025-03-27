"""
Main application for the API Gateway.

This file initializes the FastAPI application, adds middleware,
and includes routes for the API Gateway.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import prometheus_client
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse, Response
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from app.core.config import settings
from app.db.session import init_db
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.metrics import PrometheusMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# Import route modules
# from app.api.routes import api_router

# Setup logger
logger = logging.getLogger("api_gateway")

# Create FastAPI application
app = FastAPI(
    title=settings.GATEWAY_NAME,
    description="API Gateway for Natal Astrology Engine",
    version="1.0.0",
    docs_url=None,  # Disable default docs URL, we'll create a custom one
    redoc_url=None,  # Disable default redoc URL
    openapi_url="/openapi.json",
)

# Add middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(AuthMiddleware)
if settings.REDIS_URL:  # Add rate limiting only if Redis is available
    app.add_middleware(RateLimitMiddleware)

# Add CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Startup event
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize components on application startup"""
    # Initialize database
    init_db()
    logger.info(f"API Gateway database initialized successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup resources on application shutdown"""
    logger.info("API Gateway shutting down")


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    """Handle HTTP exceptions with proper logging"""
    correlation_id = getattr(request.state, "correlation_id", None)
    logger.error(
        f"HTTP {exc.status_code}: {exc.detail} "
        f"(Correlation ID: {correlation_id})"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers if hasattr(exc, "headers") else None,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> Response:
    """Handle all other exceptions with proper logging"""
    correlation_id = getattr(request.state, "correlation_id", None)
    logger.error(
        f"Unhandled exception: {str(exc)} "
        f"(Correlation ID: {correlation_id})",
        exc_info=True
    )
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Add routes
# app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "version": "1.0.0",
    }


# Metrics endpoint
@app.get("/metrics", tags=["monitoring"])
async def metrics() -> Response:
    """Expose Prometheus metrics"""
    return Response(
        content=prometheus_client.generate_latest(),
        media_type="text/plain"
    )


# Custom API docs
@app.get("/docs", tags=["documentation"])
async def get_documentation() -> HTMLResponse:
    """Custom Swagger UI docs"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.GATEWAY_NAME} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """Root endpoint with API information"""
    return {
        "name": settings.GATEWAY_NAME,
        "version": "1.0.0",
        "description": "API Gateway for Natal Astrology Engine",
        "docs_url": "/docs",
        "metrics_url": "/metrics",
        "health_url": "/health",
    }


# 404 handler
@app.get("/{path:path}", status_code=HTTP_404_NOT_FOUND)
async def not_found(path: str) -> Dict[str, Any]:
    """Handle 404 errors for any undefined route"""
    return {"detail": f"Path '/{path}' not found"}


# For local development with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)