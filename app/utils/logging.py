"""
Structured logging configuration with correlation ID support.
Provides JSON formatting for production and human-readable format for development.
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger import jsonlogger

from app.config import settings

# Context variable for correlation ID tracking
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = correlation_id_var.get()
        record.correlation_id = correlation_id if correlation_id else "N/A"
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id


def setup_logging() -> None:
    """
    Configure logging based on environment.
    JSON format for production, human-readable for development.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Add correlation ID filter
    handler.addFilter(CorrelationIDFilter())

    # Choose formatter based on environment
    if settings.is_production:
        # JSON format for production
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(logger)s %(correlation_id)s %(message)s"
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(correlation_id)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID for the current context.

    Args:
        correlation_id: Unique identifier for request tracking
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str | None:
    """
    Get the current correlation ID.

    Returns:
        Current correlation ID or None
    """
    return correlation_id_var.get()
