"""
Fallback module for directly creating FastAPI application
"""
import os
import logging
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app() -> Any:
    """
    Create a minimal FastAPI application
    
    Returns:
        FastAPI application
    """
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        # Create FastAPI app
        app = FastAPI(
            title="Natal Astrology API",
            description="Natal Astrology API Gateway Service",
            version="1.0.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add root endpoint
        @app.get("/api")
        async def root():
            return {
                "name": "Natal Astrology API",
                "version": "1.0.0",
                "status": "running"
            }
            
        # Add health check endpoint
        @app.get("/api/health")
        async def health():
            return {
                "status": "ok",
                "service": "api_gateway"
            }
        
        return app
        
    except ImportError as e:
        logger.error(f"Failed to create FastAPI app: {str(e)}")
        return None