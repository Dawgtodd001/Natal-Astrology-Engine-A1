"""
Settings for the API Gateway service

This module provides the settings for the API Gateway service.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Set

import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    API Gateway settings
    
    Attributes loaded from environment variables
    """
    # Application settings
    APP_NAME: str = "Natal Astrology API Gateway"
    APP_DESCRIPTION: str = "Gateway service for the Natal Astrology microservices"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"  # development, test, production
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # API settings
    OPENAPI_URL: str = "/api/openapi.json"
    API_KEY_HEADER: str = "X-API-Key"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Database settings
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost/natal_astrology")
    
    # Redis settings
    REDIS_URL: Optional[str] = os.environ.get("REDIS_URL", None)
    REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.environ.get("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.environ.get("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.environ.get("REDIS_PASSWORD", None)
    
    # Service URLs
    SERVICE_CHART_CALCULATION: str = os.environ.get("SERVICE_CHART_CALCULATION", "http://chart-calculation:8001")
    SERVICE_INTERPRETATION: str = os.environ.get("SERVICE_INTERPRETATION", "http://interpretation:8002")
    SERVICE_USER_PROFILE: str = os.environ.get("SERVICE_USER_PROFILE", "http://user-profile:8003")
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Feature flags
    ENABLE_METRICS: bool = True
    ENABLE_ASYNC_MODE: bool = True
    
    # Model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        use_enum_values=True,
    )


# Create settings instance
settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
)