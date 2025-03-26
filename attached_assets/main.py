"""
FastAPI application for Natal Astrology Engine
"""
import os
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as api_router
from app.api.middlewares import setup_middlewares
from app.database import init_db

# Create FastAPI app
app = FastAPI(
    title="Natal Astrology Engine",
    description="API for generating and interpreting astrological birth charts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up middlewares
setup_middlewares(app)

# Include API router
app.include_router(api_router, prefix="")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root path
@app.get("/")
async def read_root():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
