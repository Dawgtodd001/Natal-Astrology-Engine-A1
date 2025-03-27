"""
Service model for the API Gateway.

This model stores information about microservices registered with the API Gateway.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import expression, func

from app.db.base_class import Base


class Service(Base):
    """Microservice registry model"""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Connection details
    base_url = Column(String(200), nullable=False)  # e.g., "http://chart-service:8000"
    health_check_url = Column(String(200), nullable=True)  # Optional URL for health checks
    
    # Status
    is_active = Column(Boolean, default=True, server_default=expression.true())
    
    # Authentication
    requires_authentication = Column(Boolean, default=True, server_default=expression.true())
    auth_key = Column(String(100), nullable=True)  # Authentication key for the service (if required)
    
    # Configuration
    timeout_seconds = Column(Integer, default=30)  # Request timeout in seconds
    max_retries = Column(Integer, default=3)  # Number of retries for failed requests
    
    # Rate limiting (global service limits)
    rate_limit = Column(Integer, default=0)  # Requests per minute (0 means no limit)
    
    # Circuit breaking
    circuit_breaker_enabled = Column(Boolean, default=True, server_default=expression.true())
    error_threshold = Column(Integer, default=50)  # Percentage of errors to trigger circuit breaker
    
    # Metrics and monitoring
    collect_metrics = Column(Boolean, default=True, server_default=expression.true())
    
    # Audit information
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        """String representation of the service"""
        return f"<Service(id={self.id}, name={self.name}, active={self.is_active})>"
        
    def to_dict(self) -> dict:
        """Convert to dictionary (for JSON responses, etc.)"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "base_url": self.base_url,
            "health_check_url": self.health_check_url,
            "is_active": self.is_active,
            "requires_authentication": self.requires_authentication,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "rate_limit": self.rate_limit,
            "circuit_breaker_enabled": self.circuit_breaker_enabled,
            "error_threshold": self.error_threshold,
            "collect_metrics": self.collect_metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }