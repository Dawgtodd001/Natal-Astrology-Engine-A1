"""
Base imports for the API Gateway service database

This module imports all database models to ensure they are registered with SQLAlchemy.
"""

# Import base class
from api_gateway.app.db.base_class import Base

# Import all models
from api_gateway.app.models.api_key import APIKey
# Import additional models as they are created
# from api_gateway.app.models.other_model import OtherModel