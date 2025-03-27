"""
Health check endpoint for the API Gateway service

This module provides endpoints for checking the health of the API Gateway and its downstream services.
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List

import httpx
import redis
from sqlalchemy.exc import SQLAlchemyError

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

from api_gateway.app.core.settings import settings
from api_gateway.app.db.session import get_db

# Get logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/", summary="Check API Gateway health")
async def health_check() -> JSONResponse:
    """
    Check health of API Gateway and downstream services
    
    Returns:
        JSONResponse: Health status of API Gateway and downstream services
    """
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "api_gateway": {
            "status": "healthy",
            "version": settings.APP_VERSION,
        },
        "database": get_database_health(),
        "redis": await get_redis_health(),
        "services": await get_services_health(),
        "uptime": get_uptime(),
    }
    
    # Set overall status based on component health
    if any(component.get("status") == "unhealthy" for component in health_status.values() if isinstance(component, dict)):
        health_status["status"] = "degraded"
    
    # Add response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Log health check results (only errors to avoid log spam)
    if health_status["status"] != "healthy":
        logger.warning(f"Health check returned degraded status: {json.dumps(health_status)}")
    
    return JSONResponse(
        content=health_status,
        status_code=HTTP_200_OK
    )


def get_database_health() -> Dict[str, Any]:
    """
    Check database health
    
    Returns:
        Dict: Database health status
    """
    try:
        # Try to get a database session
        db = next(get_db())
        # Execute a simple query
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "connection": settings.SQLALCHEMY_DATABASE_URI.split("@")[-1] if "@" in settings.SQLALCHEMY_DATABASE_URI else "local",
        }
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error in database health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def get_redis_health() -> Dict[str, Any]:
    """
    Check Redis health
    
    Returns:
        Dict: Redis health status
    """
    if not settings.REDIS_URL and not settings.REDIS_HOST:
        return {
            "status": "disabled",
            "message": "Redis is not configured",
        }
    
    try:
        # Create Redis client
        redis_url = settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        r = redis.Redis.from_url(redis_url)
        
        # Ping Redis
        if r.ping():
            info = r.info()
            return {
                "status": "healthy",
                "version": info.get("redis_version", "unknown"),
                "memory_used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "connected_clients": info.get("connected_clients", 0),
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Redis ping failed",
            }
    except redis.RedisError as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error in Redis health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def get_services_health() -> Dict[str, Any]:
    """
    Check health of downstream services
    
    Returns:
        Dict: Health status of downstream services
    """
    services = {
        "chart_calculation": settings.SERVICE_CHART_CALCULATION,
        "interpretation": settings.SERVICE_INTERPRETATION,
        "user_profile": settings.SERVICE_USER_PROFILE,
    }
    
    results = {}
    
    # Set timeout to avoid long waits
    timeout = httpx.Timeout(2.0, connect=1.0)
    
    for name, url in services.items():
        if not url:
            results[name] = {
                "status": "disabled",
                "message": "Service is not configured",
            }
            continue
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                service_health_url = f"{url}/api/health"
                response = await client.get(service_health_url)
                
                if response.status_code == 200:
                    results[name] = {
                        "status": "healthy",
                        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    }
                else:
                    results[name] = {
                        "status": "unhealthy",
                        "response_code": response.status_code,
                        "error": "Non-200 response",
                    }
        except httpx.RequestError as e:
            logger.warning(f"Health check for {name} service failed: {e}")
            results[name] = {
                "status": "unhealthy",
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"Unexpected error in service health check for {name}: {e}")
            results[name] = {
                "status": "unhealthy",
                "error": str(e),
            }
    
    return results


def get_uptime() -> Dict[str, Any]:
    """
    Get system uptime information
    
    Returns:
        Dict: System uptime information
    """
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
            
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "seconds": round(uptime_seconds),
            "formatted": f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s",
        }
    except Exception as e:
        logger.error(f"Error getting uptime: {e}")
        return {
            "seconds": 0,
            "error": str(e),
        }