"""
FastAPI application for Natal Astrology Engine
"""
import os
import uuid
import logging
import traceback
from fastapi import FastAPI, Depends, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

from app.api.endpoints import router as api_router
from app.api.cache_monitoring import router as cache_router
from app.api.middlewares import setup_middlewares
from app.database import init_db
from app.utils.logging import setup_logging, get_logger
from app.utils.error_handling import handle_exception, ErrorCodes
from app.utils.redis_cache import is_redis_available

# Set up structured logging
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Natal Astrology Engine",
    description="API for generating and interpreting astrological birth charts",
    version="1.0.0",
    # Set docs URLs without the /api prefix since we'll add it with the router
    docs_url="/docs",  
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up middlewares
setup_middlewares(app)

# Include API routers
# This will make all routes, including the docs, available under /api prefix
app.include_router(api_router, prefix="/api")

# Include cache monitoring router under /cache
app.include_router(cache_router, prefix="/cache", tags=["Cache Monitoring"])

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted successfully")
except Exception as e:
    logger.warning(f"Could not mount static files: {str(e)}")
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    # Try mounting again
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Comprehensive exception handlers for better logging and user experience

# Handle general exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions
    """
    # Get traceback information
    import traceback
    tb_str = ''.join(traceback.format_tb(exc.__traceback__))
    
    # Log detailed error information
    logger.error(
        f"Unhandled exception in request {request.method} {request.url}",
        extra={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else "unknown",
            "traceback": tb_str
        }
    )
    
    # Return a clean response to the client
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "type": type(exc).__name__,
            "request_id": str(uuid.uuid4()),  # Add a unique ID for tracking in logs
        }
    )

# Handle validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for validation errors with clear user feedback
    """
    # Extract validation error details
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        loc = " -> ".join(str(x) for x in error["loc"] if x != "body")
        error_messages.append(f"{loc}: {error['msg']}")
    
    # Log validation errors at warning level
    logger.warning(
        f"Validation error in request {request.method} {request.url}",
        extra={
            "errors": errors,
            "path": request.url.path
        }
    )
    
    # Return structured error response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "errors": error_messages
            }
        }
    )

# Handle HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Enhanced HTTP exception handler with logging
    """
    # Log HTTP exceptions at info level for 4xx errors and error level for others
    log_level = "info" if 400 <= exc.status_code < 500 else "error"
    
    log_method = getattr(logger, log_level)
    log_method(
        f"HTTP exception: {exc.status_code} in {request.method} {request.url}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path
        }
    )
    
    # Return the exception response with some additional context
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

# Serve index.html at root path
@app.get("/")
async def read_root():
    from fastapi.responses import FileResponse
    logger.info("Serving index page")
    
    # Check if index.html exists, create a minimal one if not
    if not os.path.exists("static/index.html"):
        logger.info("Creating minimal index.html")
        os.makedirs("static", exist_ok=True)
        with open("static/index.html", "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Natal Astrology API</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
                    h1 { color: #2c3e50; }
                    a { color: #3498db; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                    .container { border: 1px solid #eee; border-radius: 5px; padding: 20px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <h1>Natal Astrology API</h1>
                <p>Welcome to the Natal Astrology API service. This API provides astrological chart analysis and interpretations.</p>
                <div class="container">
                    <h2>API Documentation</h2>
                    <p>Explore the API using the interactive documentation:</p>
                    <ul>
                        <li><a href="/api/docs">Swagger UI Documentation</a></li>
                        <li><a href="/api/redoc">ReDoc Documentation</a></li>
                    </ul>
                </div>
            </body>
            </html>
            """)
    
    return FileResponse("static/index.html")

# Initialize database and check Redis on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting application")
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Check Redis availability
        redis_available = is_redis_available()
        if redis_available:
            logger.info("Redis cache is available")
        else:
            logger.warning("Redis cache is not available - performance may be degraded")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")
