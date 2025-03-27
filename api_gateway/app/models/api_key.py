"""
API Key model for the API Gateway service

This module defines the SQLAlchemy model for API keys.
"""

import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.sql import func

from api_gateway.app.db.base_class import Base


class APIKey(Base):
    """
    API Key model for authentication and authorization
    
    Attributes:
        id: Primary key
        key: API key string (UUID)
        name: Name of the API key
        user_id: ID of user associated with the API key
        is_active: Whether the API key is active
        permissions: Comma-separated list of permissions
        created_at: When the API key was created
        expires_at: When the API key expires (optional)
        last_used_at: When the API key was last used
    """
    
    __tablename__ = "api_keys"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    key = sa.Column(sa.String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = sa.Column(sa.String(255), nullable=False)
    user_id = sa.Column(sa.Integer, nullable=False)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    permissions = sa.Column(sa.String(1024), nullable=True)
    created_at = sa.Column(sa.DateTime, default=func.now(), nullable=False)
    expires_at = sa.Column(sa.DateTime, nullable=True)
    last_used_at = sa.Column(sa.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<APIKey id={self.id} name={self.name} user_id={self.user_id}>"