"""
Structured logging utilities for the application
"""
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

class StructuredLogFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logs
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "line": record.lineno,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # Add any extra attributes passed to the logger
        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)
            
        return json.dumps(log_data)

def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up structured logging for the application
    
    Args:
        level: Logging level (default: INFO)
    """
    # Reset root logger in case it was configured elsewhere
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    
    # Configure root logger
    root.setLevel(level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredLogFormatter())
    root.addHandler(handler)
    
    # Log setup complete
    logger = get_logger("app.utils.logging")
    logger.info("Structured logging initialized", extra={"log_level": logging.getLevelName(level)})

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)

def log_with_context(
    logger: logging.Logger, 
    level: int, 
    message: str, 
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a message with additional context
    
    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        extra: Additional context to include in the log
    """
    if extra is None:
        extra = {}
    
    # Create a LogRecord with extra context
    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.extra = extra
    
    # Format and emit the log
    for handler in logger.handlers:
        handler.handle(record)