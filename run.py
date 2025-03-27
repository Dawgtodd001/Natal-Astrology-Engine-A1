"""
Server startup script for Natal Astrology Engine
"""
import os
import logging
import argparse
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Import settings
from shared.config.settings import settings

# Import Redis utilities
from shared.utils.redis_client import is_redis_available


def _setup_sentry():
    """Setup Sentry error tracking if configured"""
    sentry_dsn = os.getenv("SENTRY_DSN")
    
    if not sentry_dsn:
        logger.info("Sentry DSN not provided, skipping Sentry initialization")
        return
        
    try:
        import sentry_sdk
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        
        # Extra integrations for specific services
        integrations = [
            SqlalchemyIntegration(),
            RedisIntegration()
        ]
        
        # Add more integrations based on available packages
        try:
            from sentry_sdk.integrations.celery import CeleryIntegration
            integrations.append(CeleryIntegration())
        except ImportError:
            pass
            
        try:
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            integrations.append(FastApiIntegration())
        except ImportError:
            pass
            
        # Initialize Sentry SDK
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=settings.APP_ENV,
            release=settings.APP_VERSION,
            integrations=integrations,
            traces_sample_rate=0.1,
            send_default_pii=False,
            attach_stacktrace=True,
        )
        
        logger.info("Sentry initialized successfully")
        
    except ImportError:
        logger.warning("Sentry SDK not installed, error tracking disabled")
    except Exception as e:
        logger.error(f"Error initializing Sentry: {str(e)}")


def check_redis():
    """Check Redis availability and report status"""
    if is_redis_available():
        logger.info("✅ Redis is available")
        return True
    else:
        logger.warning("⚠️ Redis is not available - caching and async tasks will be disabled")
        return False


def check_system_health():
    """Perform system health checks before startup"""
    # Check Redis
    redis_available = check_redis()
    
    # Add more health checks here
    
    return {
        "redis": redis_available
    }
    

def start_fastapi_app():
    """Start FastAPI server using Uvicorn"""
    try:
        import uvicorn
        from fastapi import FastAPI
        
        # Load the FastAPI app 
        try:
            from services.api_gateway.app import create_app
            app = create_app()
        except ImportError as e:
            logger.warning(f"Error importing API gateway: {str(e)}")
            # Fallback to direct app creation if the import fails
            from services.api_gateway.app_py import create_app
            app = create_app()
        
        # Start the server with Uvicorn
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        
        logger.info(f"Starting FastAPI server on {host}:{port}")
        uvicorn.run(
            app, 
            host=host, 
            port=port,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True
        )
        
    except ImportError as e:
        logger.error(f"Required package not found: {str(e)}")
        
    except Exception as e:
        logger.exception(f"Error starting FastAPI server: {str(e)}")


def start_celery_worker():
    """Start Celery worker for background task processing"""
    try:
        from shared.utils.celery_app import celery_app
        
        if celery_app is None:
            logger.error("Celery not available, worker not started")
            return
            
        # Start worker
        logger.info("Starting Celery worker")
        argv = [
            'worker',
            '--loglevel=INFO',
            '--concurrency=1'
        ]
        
        # Check if Redis is available before starting
        if not is_redis_available():
            logger.error("Redis not available, Celery worker cannot start")
            return
            
        celery_app.worker_main(argv)
        
    except ImportError as e:
        logger.error(f"Required package not found: {str(e)}")
        
    except Exception as e:
        logger.exception(f"Error starting Celery worker: {str(e)}")


def main():
    """Main entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Natal Astrology Engine Service")
    parser.add_argument(
        "--server",
        choices=["fastapi", "celery"],
        default="fastapi",
        help="Server type to start: fastapi or celery"
    )
    args = parser.parse_args()
    
    # Setup Sentry for error tracking
    _setup_sentry()
    
    # Run health checks
    health_status = check_system_health()
    
    # Display application info
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    
    # Start requested server
    if args.server == "fastapi":
        start_fastapi_app()
    elif args.server == "celery":
        start_celery_worker()
    else:
        logger.error(f"Unknown server type: {args.server}")


if __name__ == "__main__":
    main()