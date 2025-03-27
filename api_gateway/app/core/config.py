"""
Configuration settings for the API Gateway.

This file contains all configuration settings for the API Gateway.
"""

import os
import logging
import secrets
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, validator
from pydantic_settings import BaseSettings

logger = logging.getLogger("api_gateway")


class Settings(BaseSettings):
    """API Gateway configuration settings"""
    
    # API Gateway information
    API_GATEWAY_NAME: str = "Natal Astrology API Gateway"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Natal Astrology API Gateway"
    
    # Security settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Database connection
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./api_gateway.db")
    
    # Database pool settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    # Redis connection for caching and rate limiting
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # Rate limiting
    DEFAULT_RATE_LIMIT: int = 60  # Requests per minute
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Other settings
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str = "changeme"
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        Parse CORS origins from string or list
        
        Args:
            v: CORS origins as string or list
            
        Returns:
            List of CORS origins
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
        
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: Optional[str]) -> str:
        """
        Validate database URL
        
        Args:
            v: Database URL
            
        Returns:
            Valid database URL
        """
        if not v:
            return "sqlite:///./api_gateway.db"
        return v
        
    @validator("REDIS_URL", pre=True)
    def validate_redis_url(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate Redis URL
        
        Args:
            v: Redis URL
            
        Returns:
            Valid Redis URL or None
        """
        if not v:
            logger.warning("No Redis URL provided, rate limiting and caching will be disabled")
            return None
        return v
        
    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance and cache it
@lru_cache()
def get_settings() -> Settings:
    """
    Get settings instance (cached)
    
    Returns:
        Settings instance
    """
    return Settings()


settings = get_settings()