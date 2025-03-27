"""
Base class for SQLAlchemy models in the API Gateway service

This module defines the base class used by all SQLAlchemy models.
"""

import logging
from typing import Any, Dict, TypeVar

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import registry

# Get logger
logger = logging.getLogger(__name__)

# Create a registry for mapping classes to tables
mapper_registry = registry()

# TypeVar for self-referencing
T = TypeVar("T", bound="Base")


@as_declarative(metadata=mapper_registry.metadata)
class Base:
    """
    Base class for all SQLAlchemy models
    
    Attributes:
        id: Primary key
        __name__: Table name automatically derived from class name
    """
    
    # All models have an ID
    id: Any
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name
        
        Returns:
            Table name (derived from class name, lowercase with underscores)
        """
        # Convert CamelCase to snake_case for table names
        result = ""
        for i, char in enumerate(cls.__name__):
            if char.isupper() and i > 0:
                result += "_" + char.lower()
            else:
                result += char.lower()
        return result