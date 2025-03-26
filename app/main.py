"""
FastAPI application for Natal Astrology Engine
"""
import os
import logging
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.endpoints import router as api_router
from app.api.middlewares import setup_middlewares
from app.database import init_db
from app.utils.logging import setup_logging, get_logger
from app.utils.error_handling import handle_exception, ErrorCodes

# Set up structured logging
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Natal Astrology Engine",
    description="API for generating and interpreting astrological birth charts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# Include API router
app.include_router(api_router, prefix="")

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

# Add exception handler for better logging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception in request {request.method} {request.url}",
        extra={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else "unknown"
        }
    )
    
    # Return a clean response to the client
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
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
                        <li><a href="/docs">Swagger UI Documentation</a></li>
                        <li><a href="/redoc">ReDoc Documentation</a></li>
                    </ul>
                </div>
            </body>
            </html>
            """)
    
    return FileResponse("static/index.html")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting application")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")
