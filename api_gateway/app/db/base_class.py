"""
Base model class for the API Gateway.

This file defines the base class used by all SQLAlchemy models.
"""

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative

@as_declarative()
class Base:
    """Base class for all ORM models"""
    
    # Generate tablename automatically
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate tablename from class name"""
        return cls.__name__.lower()
        
    # Add convenient methods for all models
    def dict(self):
        """Convert model instance to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}