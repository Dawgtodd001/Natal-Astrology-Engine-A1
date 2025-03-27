"""
Database session management for the API Gateway service

This module provides functions and classes for managing database sessions.
"""

import logging
import contextlib
from functools import wraps
from typing import Iterator, AsyncIterator, Any, Dict, Optional, Callable, TypeVar, cast

import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, Session

from api_gateway.app.core.settings import settings

# Get logger
logger = logging.getLogger(__name__)

# Type variable for decorators
T = TypeVar("T")

# Create engine based on configuration
if settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql+asyncpg"):
    # Async engine for asyncpg
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=settings.SQL_ECHO,
        future=True,
        pool_pre_ping=True,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
    )
    
    # Create async session factory
    async_session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
else:
    # Sync engine for other database types
    engine = sqlalchemy.create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=settings.SQL_ECHO,
        future=True,
        pool_pre_ping=True,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
    )
    
    # Create sync session factory
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )


def get_db() -> Iterator[Session]:
    """
    Get a database session
    Used as a dependency in FastAPI endpoints
    
    Returns:
        SQLAlchemy database session that will be closed after usage
        
    Raises:
        HTTPException: If database connection fails
    """
    if not hasattr(get_db, "session_factory"):
        raise RuntimeError("Database session factory not properly initialized")
        
    db = session_factory()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextlib.contextmanager
def get_db_context() -> Iterator[Session]:
    """
    Get a database session as a context manager
    
    Returns:
        SQLAlchemy database session that will be closed after usage
        
    Example:
        with get_db_context() as db:
            result = db.query(Model).all()
    """
    if not hasattr(get_db, "session_factory"):
        raise RuntimeError("Database session factory not properly initialized")
        
    db = session_factory()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def get_async_db() -> AsyncIterator[AsyncSession]:
    """
    Get an async database session
    Used as a dependency in FastAPI endpoints
    
    Returns:
        SQLAlchemy async database session that will be closed after usage
        
    Raises:
        HTTPException: If database connection fails
    """
    if not hasattr(get_async_db, "async_session_factory"):
        raise RuntimeError("Async database session factory not properly initialized")
        
    async_db = async_session_factory()
    try:
        yield async_db
    except Exception as e:
        logger.error(f"Async database session error: {e}")
        await async_db.rollback()
        raise
    finally:
        await async_db.close()


@contextlib.asynccontextmanager
async def get_async_db_context() -> AsyncIterator[AsyncSession]:
    """
    Get an async database session as a context manager
    
    Returns:
        SQLAlchemy async database session that will be closed after usage
        
    Example:
        async with get_async_db_context() as db:
            result = await db.execute(select(Model))
    """
    if not hasattr(get_async_db, "async_session_factory"):
        raise RuntimeError("Async database session factory not properly initialized")
        
    async_db = async_session_factory()
    try:
        yield async_db
    except Exception as e:
        logger.error(f"Async database session error: {e}")
        await async_db.rollback()
        raise
    finally:
        await async_db.close()


def with_db_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to provide a database session to a function
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with database session as first argument
        
    Example:
        @with_db_session
        def get_user(db, user_id):
            return db.query(User).filter(User.id == user_id).first()
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        with get_db_context() as db:
            return cast(T, func(db, *args, **kwargs))
    return wrapper


def async_with_db_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to provide an async database session to a function
    
    Args:
        func: Async function to wrap
        
    Returns:
        Wrapped async function with database session as first argument
        
    Example:
        @async_with_db_session
        async def get_user(db, user_id):
            result = await db.execute(select(User).filter(User.id == user_id))
            return result.scalar_one_or_none()
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        async with get_async_db_context() as db:
            return cast(T, await func(db, *args, **kwargs))
    return wrapper