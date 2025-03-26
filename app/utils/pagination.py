"""
Pagination utilities for API endpoints
"""
from typing import TypeVar, Generic, List, Type, Any, Dict, Callable, Optional
from sqlalchemy.orm import Query
from sqlalchemy.orm import Session

from app.api.schemas import PaginationParams, PageInfo, PaginatedResponse

T = TypeVar('T')
M = TypeVar('M')  # SQLAlchemy model type

def paginate_query(
    query: Query,
    pagination: PaginationParams,
    model_to_schema: Callable[[M], T]
) -> PaginatedResponse[T]:
    """
    Paginate a SQLAlchemy query and convert results to Pydantic models
    
    Args:
        query: SQLAlchemy query object
        pagination: Pagination parameters
        model_to_schema: Function to convert DB model to API schema
        
    Returns:
        Paginated response with items and pagination metadata
    """
    # Get total count
    total_count = query.count()
    
    # Calculate offset
    offset = (pagination.page - 1) * pagination.page_size
    
    # Get paginated results
    items = query.offset(offset).limit(pagination.page_size).all()
    
    # Calculate pagination metadata
    total_pages = (total_count + pagination.page_size - 1) // pagination.page_size if total_count > 0 else 1
    has_next = pagination.page < total_pages
    has_prev = pagination.page > 1
    
    # Convert to API response objects
    schema_items = [model_to_schema(item) for item in items]
    
    # Build page info
    page_info = PageInfo(
        current_page=pagination.page,
        page_size=pagination.page_size,
        total_items=total_count,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
    
    # Return paginated response
    return PaginatedResponse[T](
        items=schema_items,
        page_info=page_info
    )