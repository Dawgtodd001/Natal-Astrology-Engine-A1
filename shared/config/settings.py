"""
Shared configuration settings for all microservices
"""
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Try to import pydantic, but provide fallbacks if not available
try:
    from pydantic import BaseModel
except ImportError:
    # Simple fallback implementation if pydantic is not available
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
                
        class Config:
            case_sensitive = True
            env_prefix = ""


class Settings(BaseModel):
    """
    Shared global settings for all microservices
    
    This ensures consistent configuration across services
    """
    # Base settings
    APP_NAME: str = os.getenv("APP_NAME", "Natal Astrology Engine")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_DESCRIPTION: str = os.getenv("APP_DESCRIPTION", 
                                     "API for calculating and interpreting natal astrology charts")
    
    # Environment and debugging
    APP_ENV: str = os.getenv("APP_ENV", "development")  # development, staging, production
    
    # Performance and scaling
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    WORKER_CONNECTIONS: int = int(os.getenv("WORKER_CONNECTIONS", "1000"))
    
    # CORS settings
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "natal_astrology_super_secret_key_change_this_in_production")
    API_KEY_HEADER: str = "X-API-Key"
    
    # Service discovery
    SERVICE_REGISTRY_HOST: str = os.getenv("SERVICE_REGISTRY_HOST", "localhost")
    SERVICE_REGISTRY_PORT: int = int(os.getenv("SERVICE_REGISTRY_PORT", "8500"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    STRUCTURED_LOGGING: bool = os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"
    
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"postgresql://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('PGDATABASE')}"
    )
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "300"))
    
    # Metrics and monitoring
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL: str = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    
    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_TASK_TIMEOUT: float = float(os.getenv("CELERY_TASK_TIMEOUT", "300.0"))  # 5 minutes
    
    # API Gateway settings
    API_GATEWAY_HOST: str = os.getenv("API_GATEWAY_HOST", "localhost")
    API_GATEWAY_PORT: int = int(os.getenv("API_GATEWAY_PORT", "8000"))
    
    # Service URLs with fallbacks to local development settings
    API_GATEWAY_URL: str = os.getenv("API_GATEWAY_URL", f"http://{API_GATEWAY_HOST}:{API_GATEWAY_PORT}")
    CHART_SERVICE_URL: str = os.getenv("CHART_SERVICE_URL", "http://localhost:8001")
    INTERPRET_SERVICE_URL: str = os.getenv("INTERPRET_SERVICE_URL", "http://localhost:8002")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://localhost:8003")

    # OpenAI settings for AI interpretation
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    
    # Class configuration
    class Config:
        case_sensitive = True
        env_prefix = ""

    def as_dict(self) -> Dict[str, Any]:
        """Convert settings to a dictionary"""
        return {key: value for key, value in self.__dict__.items() 
                if not key.startswith("_") and not callable(value)}
    
    def as_json(self) -> str:
        """Convert settings to a JSON string"""
        return json.dumps(self.as_dict(), indent=2)
    
    def get_service_url(self, service_name: str) -> str:
        """Get URL for a specific service"""
        service_map = {
            "api-gateway": self.API_GATEWAY_URL,
            "chart-calculation": self.CHART_SERVICE_URL,
            "interpretation": self.INTERPRET_SERVICE_URL,
            "user-profile": self.USER_SERVICE_URL,
        }
        
        return service_map.get(service_name.lower(), "")


# Create global settings instance
settings = Settings()

# Export to make available as an import
__all__ = ["settings", "Settings"]