"""
API router for version 1 endpoints

This module collects all API endpoint routers and combines them into a single router.
"""

from fastapi import APIRouter

from api_gateway.app.api.api_v1.endpoints import health, charts, interpretations, users

# Create API router
api_router = APIRouter()

# Add health router
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Add charts router
api_router.include_router(charts.router, prefix="/charts", tags=["charts"])

# Add interpretations router
api_router.include_router(interpretations.router, prefix="/interpretations", tags=["interpretations"])

# Add users router
api_router.include_router(users.router, prefix="/users", tags=["users"])