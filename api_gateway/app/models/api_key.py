"""
API Key model for the API Gateway.

This model stores API keys used for authentication and access control.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import expression, func

from app.db.base_class import Base


class ApiKey(Base):
    """API key model for authentication and access control"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    enabled = Column(Boolean, default=True, server_default=expression.true())
    
    # Rate limits
    rate_limit = Column(Integer, default=60)  # Requests per minute
    daily_limit = Column(Integer, default=1000)  # Requests per day
    
    # Permissions
    can_access_chart_service = Column(Boolean, default=True, server_default=expression.true())
    can_access_interpretation_service = Column(Boolean, default=True, server_default=expression.true())
    can_access_user_profile_service = Column(Boolean, default=False, server_default=expression.false())
    
    # API Key type (admin, read-only, write, etc.)
    is_admin = Column(Boolean, default=False, server_default=expression.false())
    
    # Usage tracking
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    last_used = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the API key"""
        return f"<ApiKey(id={self.id}, name={self.name}, enabled={self.enabled})>"
        
    def to_dict(self) -> dict:
        """Convert to dictionary (for JSON responses, etc.)"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "rate_limit": self.rate_limit,
            "daily_limit": self.daily_limit,
            "can_access_chart_service": self.can_access_chart_service,
            "can_access_interpretation_service": self.can_access_interpretation_service,
            "can_access_user_profile_service": self.can_access_user_profile_service,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }