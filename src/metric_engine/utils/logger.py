"""
Logging utilities for the metric engine.
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None,
    include_metrics: bool = True
) -> logging.Logger:
    """
    Setup logging for the metric engine.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format_type: Format type ("json" or "text")
        log_file: Optional log file path
        include_metrics: Whether to include metrics in logs
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger("metric_engine")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "metric_engine") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def log_operation(
    logger: logging.Logger,
    operation: str,
    **kwargs: Any
) -> None:
    """
    Log an operation with structured data.
    
    Args:
        logger: Logger instance
        operation: Operation name
        **kwargs: Additional fields to log
    """
    extra_fields = {"operation": operation, **kwargs}
    logger.info(
        f"Operation: {operation}",
        extra={"extra_fields": extra_fields}
    )

