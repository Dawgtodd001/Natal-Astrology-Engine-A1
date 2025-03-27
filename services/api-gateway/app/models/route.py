"""
Route model for the API Gateway.

This model stores API routes and their mapping to services.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import expression, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Route(Base):
    """API route mapping model"""

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(200), nullable=False, index=True)  # e.g., "/api/v1/chart/calculate"
    description = Column(Text, nullable=True)
    
    # Method
    method = Column(String(10), nullable=False, default="GET")  # GET, POST, PUT, DELETE, etc.
    
    # Service mapping
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    service = relationship("Service", backref="routes")
    
    # Target endpoint
    target_path = Column(String(200), nullable=False)  # e.g., "/chart/calculate" - path on the target service
    
    # Access control
    public = Column(Boolean, default=False, server_default=expression.false())  # If True, no authentication needed
    admin_only = Column(Boolean, default=False, server_default=expression.false())  # If True, only admin API keys can access
    
    # Rate limiting
    rate_limit_enabled = Column(Boolean, default=True, server_default=expression.true())
    rate_limit = Column(Integer, default=0)  # Overrides service and API key rate limits if > 0
    
    # Caching
    cache_enabled = Column(Boolean, default=False, server_default=expression.false())
    cache_ttl = Column(Integer, default=60)  # Time to live in seconds for cached responses
    
    # Metrics and logging
    log_requests = Column(Boolean, default=True, server_default=expression.true())
    collect_metrics = Column(Boolean, default=True, server_default=expression.true())
    
    # Audit information
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        """String representation of the route"""
        return f"<Route(id={self.id}, path={self.path}, method={self.method})>"
        
    def to_dict(self) -> dict:
        """Convert to dictionary (for JSON responses, etc.)"""
        return {
            "id": self.id,
            "path": self.path,
            "description": self.description,
            "method": self.method,
            "service_id": self.service_id,
            "target_path": self.target_path,
            "public": self.public,
            "admin_only": self.admin_only,
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit": self.rate_limit,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "log_requests": self.log_requests,
            "collect_metrics": self.collect_metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }