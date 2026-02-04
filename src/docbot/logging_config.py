"""Structured JSON logging with request correlation."""

import logging
import sys
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger import jsonlogger


# Context variable for request correlation
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    """Add request_id to log records from context variable."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id from context to record."""
        request_id = request_id_var.get("")
        if request_id:
            record.request_id = request_id
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with consistent field names."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any]
    ) -> None:
        """Add standard fields to JSON log output."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger_name"] = record.name
        log_record["message"] = record.getMessage()

        # Add request_id if present
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured JSON logging for the application.

    All logs are output as one JSON object per line to stdout.
    Includes timestamp, level, logger_name, message, and optional request_id.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    json_formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(logger_name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S.%fZ"
    )
    console_handler.setFormatter(json_formatter)

    # Add request ID filter
    console_handler.addFilter(RequestIdFilter())

    # Configure root logger
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Suppress noisy uvicorn access logs (we have our own request middleware)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").propagate = False

    # Keep uvicorn error logs
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
