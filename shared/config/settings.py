"""
Shared configuration settings for the Natal Astrology Engine microservices.

This module provides common configuration settings that can be
imported and used by any microservice, ensuring consistency across
the system.
"""

import os
import secrets
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

try:
    from pydantic import BaseSettings, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseSettings = object
    Field = lambda *args, **kwargs: None  # noqa


# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Define settings class if Pydantic is available
if PYDANTIC_AVAILABLE:
    class BaseServiceSettings(BaseSettings):
        """Base settings class for all services"""
        
        # Service identification
        SERVICE_NAME: str = Field("Unknown", description="Name of the service")
        VERSION: str = Field("1.0.0", description="Service version")
        
        # API configuration
        API_V1_STR: str = Field("/api/v1", description="API v1 prefix")
        
        # Authentication
        SECRET_KEY: str = Field(
            default_factory=lambda: secrets.token_urlsafe(32),
            description="Secret key for security features"
        )
        DEFAULT_API_KEY: Optional[str] = Field(
            None, description="Default API key for development"
        )
        
        # CORS
        BACKEND_CORS_ORIGINS: List[str] = Field(
            ["*"],
            description="List of allowed origins for CORS"
        )
        
        # Database
        DATABASE_URL: str = Field(
            "sqlite:///app.db",
            description="Database connection URL"
        )
        
        # Redis
        REDIS_URL: Optional[str] = Field(
            None,
            description="Redis connection URL"
        )
        REDIS_CACHE_TTL: int = Field(
            3600,
            description="Default TTL for cached items in seconds"
        )
        
        # Logging
        LOG_LEVEL: str = Field(
            "INFO",
            description="Log level"
        )
        JSON_LOGS: bool = Field(
            True,
            description="Use JSON format for logs"
        )
        
        # Monitoring
        ENABLE_METRICS: bool = Field(
            True,
            description="Enable Prometheus metrics"
        )
        PROMETHEUS_MULTIPROC_DIR: Optional[str] = Field(
            None,
            description="Directory for Prometheus multiprocess mode"
        )
        
        # Sentry error tracking
        SENTRY_DSN: Optional[str] = Field(
            None,
            description="Sentry DSN for error tracking"
        )
        SENTRY_ENVIRONMENT: str = Field(
            "development",
            description="Sentry environment"
        )
        SENTRY_TRACES_SAMPLE_RATE: float = Field(
            0.1,
            description="Sentry traces sample rate"
        )
        
        # OpenAI
        OPENAI_API_KEY: Optional[str] = Field(
            None,
            description="OpenAI API Key for AI-powered interpretations"
        )
        
        class Config:
            env_file = ".env"
            case_sensitive = True


# If Pydantic is not available, provide a fallback
else:
    # Basic settings functions
    def get_env(key: str, default: Any = None) -> Any:
        """Get environment variable"""
        return os.environ.get(key, default)
    
    
    # Define common settings as variables
    SERVICE_NAME = get_env("SERVICE_NAME", "Unknown")
    VERSION = get_env("VERSION", "1.0.0")
    API_V1_STR = get_env("API_V1_STR", "/api/v1")
    SECRET_KEY = get_env("SECRET_KEY", secrets.token_urlsafe(32))
    DEFAULT_API_KEY = get_env("DEFAULT_API_KEY")
    BACKEND_CORS_ORIGINS = get_env("BACKEND_CORS_ORIGINS", "*").split(",")
    DATABASE_URL = get_env("DATABASE_URL", "sqlite:///app.db")
    REDIS_URL = get_env("REDIS_URL")
    REDIS_CACHE_TTL = int(get_env("REDIS_CACHE_TTL", "3600"))
    LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
    JSON_LOGS = get_env("JSON_LOGS", "true").lower() in ("true", "1", "t")
    ENABLE_METRICS = get_env("ENABLE_METRICS", "true").lower() in ("true", "1", "t")
    PROMETHEUS_MULTIPROC_DIR = get_env("PROMETHEUS_MULTIPROC_DIR")
    SENTRY_DSN = get_env("SENTRY_DSN")
    SENTRY_ENVIRONMENT = get_env("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE = float(get_env("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    OPENAI_API_KEY = get_env("OPENAI_API_KEY")