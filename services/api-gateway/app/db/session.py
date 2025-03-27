"""
Database session configuration for the API Gateway.

This file sets up the database connection and provides session management.
"""

import os
import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import Generator, Optional

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger("api_gateway")

# Create database engine based on configuration
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Check if we're using a SQLite database
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = sqlalchemy.create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
else:
    engine = sqlalchemy.create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
    )

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create an async engine if async database access is needed
if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # For PostgreSQL, MySQL, etc., create an async engine
    async_db_url = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(
        async_db_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
    )
    AsyncSessionLocal = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
else:
    # SQLite doesn't support async operations well
    # Use standard engine with a warning
    logger.warning("SQLite database doesn't support async operations efficiently")
    AsyncSessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session
    
    Yields:
        SQLAlchemy session that will be closed after usage
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> Generator[AsyncSession, None, None]:
    """
    Get an async database session
    
    Yields:
        SQLAlchemy AsyncSession that will be closed after usage
        
    Raises:
        RuntimeError: If async database is not configured
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database access is not configured")
        
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()


@contextmanager
def db_session():
    """
    Context manager for database sessions
    
    Yields:
        SQLAlchemy session that will be committed or rolled back automatically
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@lru_cache()
def get_engine():
    """
    Get the SQLAlchemy engine
    
    Returns:
        SQLAlchemy engine instance
    """
    return engine