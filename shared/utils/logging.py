"""
Shared logging configuration for the Natal Astrology Engine microservices.

This module provides a consistent logging setup across all microservices,
supporting both structured JSON logging for production and more readable
console logging for development.
"""

import json
import logging
import sys
import traceback
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union

# Attempt to get shared settings
try:
    from shared.config.settings import (
        LOG_LEVEL, 
        JSON_LOGS,
        SERVICE_NAME
    )
except ImportError:
    # Fallback to environment variables if shared settings not available
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    JSON_LOGS = os.environ.get("JSON_LOGS", "true").lower() in ("true", "1", "t")
    SERVICE_NAME = os.environ.get("SERVICE_NAME", "unknown")


class JSONLogFormatter(logging.Formatter):
    """
    Custom formatter to produce JSON-formatted logs for machine parsing.
    
    This formatter produces structured logs that can be easily indexed and
    searched by log management systems like ELK Stack or similar.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.
        
        Args:
            record: LogRecord instance
            
        Returns:
            JSON string representation of the log record
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "line": record.lineno,
        }
        
        # Add service name
        log_data["service"] = SERVICE_NAME
        
        # Add exception information if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        
        # Add extra data if available
        if hasattr(record, "data") and isinstance(record.data, dict):
            for key, value in record.data.items():
                if key not in log_data:
                    log_data[key] = value
        
        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        return json.dumps(log_data)


class ConsoleLogFormatter(logging.Formatter):
    """
    Human-readable console log formatter.
    
    This formatter produces more readable logs for development and debugging.
    """
    
    # ANSI color codes for log levels
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
        "RESET": "\033[0m",      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record for console output.
        
        Args:
            record: LogRecord instance
            
        Returns:
            Formatted string for console output
        """
        level_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset_color = self.COLORS["RESET"]
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build the base message
        formatted_message = (
            f"{timestamp} | "
            f"{level_color}{record.levelname}{reset_color} | "
            f"{record.name} | "
            f"{record.getMessage()}"
        )
        
        # Add source file information
        source_info = f" ({record.pathname}:{record.lineno})"
        formatted_message += source_info
        
        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            formatted_message += f" [correlation_id: {record.correlation_id}]"
        
        # Add exception information if available
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            formatted_message += f"\n{exc_text}"
        
        return formatted_message


def setup_logging(service_name: str = SERVICE_NAME, log_level: str = LOG_LEVEL, json_format: bool = JSON_LOGS) -> None:
    """
    Set up logging for a microservice.
    
    Args:
        service_name: Name of the service
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON format for logs
        
    This function configures logging to output either JSON-formatted logs
    for production or human-readable logs for development.
    """
    # Convert string log level to numeric value
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Set formatter based on configuration
    if json_format:
        formatter = JSONLogFormatter()
    else:
        formatter = ConsoleLogFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set specific levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Initial log to confirm setup
    logger = logging.getLogger("shared.utils.logging")
    logger.info("Structured logging initialized")


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds additional context to log records.
    
    This adapter allows adding consistent context to all log messages
    from a particular component, such as correlation IDs.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process the log message by adding context data.
        
        Args:
            msg: Log message
            kwargs: Logging keyword arguments
            
        Returns:
            Tuple of (message, kwargs) with updated context
        """
        # Add extra data to log record
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        
        # Add context from adapter
        kwargs["extra"].update(self.extra)
        
        return msg, kwargs


def get_logger(name: str, **context) -> logging.Logger:
    """
    Get a logger with optional context data.
    
    Args:
        name: Logger name
        **context: Additional context data to include in all logs
        
    Returns:
        Logger instance with context
    """
    logger = logging.getLogger(name)
    
    if context:
        return LoggerAdapter(logger, context)
    
    return logger