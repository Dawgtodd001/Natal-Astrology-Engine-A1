"""
Database initialization script for the API Gateway service

This module creates all database tables and inserts initial data.
"""

import logging
import uuid
from datetime import datetime, timedelta

import sqlalchemy as sa

from api_gateway.app.db.base import Base
from api_gateway.app.db.session import engine
from api_gateway.app.models.api_key import APIKey

# Get logger
logger = logging.getLogger(__name__)


def create_tables() -> None:
    """
    Create all database tables
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_initialized(db) -> bool:
    """
    Check if the database has been initialized
    
    Args:
        db: Database session
        
    Returns:
        True if the database has been initialized, False otherwise
    """
    try:
        # Check if API keys table exists and has at least one record
        result = db.execute(sa.text("SELECT COUNT(*) FROM api_keys")).scalar()
        return result > 0
    except Exception as e:
        logger.warning(f"Error checking if database is initialized: {e}")
        return False


def seed_initial_data(db) -> None:
    """
    Seed initial data into the database
    
    Args:
        db: Database session
    """
    try:
        # Check if we already have data
        if check_db_initialized(db):
            logger.info("Database already initialized with seed data")
            return
            
        logger.info("Seeding initial data...")
        
        # Create default API keys
        create_default_api_keys(db)
        
        logger.info("Initial data seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding initial data: {e}")
        db.rollback()
        raise


def create_default_api_keys(db) -> None:
    """
    Create default API keys
    
    Args:
        db: Database session
    """
    # Create admin API key
    admin_key = APIKey(
        key=str(uuid.uuid4()),
        name="Admin API Key",
        user_id=1,
        is_active=True,
        permissions="admin",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365)
    )
    
    # Create default user API key
    user_key = APIKey(
        key=str(uuid.uuid4()),
        name="Default User API Key",
        user_id=2,
        is_active=True,
        permissions="user",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    # Add to database
    db.add(admin_key)
    db.add(user_key)
    db.commit()
    
    logger.info(f"Created admin API key: {admin_key.key}")
    logger.info(f"Created user API key: {user_key.key}")


def init_db() -> None:
    """
    Initialize the database
    """
    from api_gateway.app.db.session import db_session
    
    create_tables()
    
    with db_session() as db:
        seed_initial_data(db)