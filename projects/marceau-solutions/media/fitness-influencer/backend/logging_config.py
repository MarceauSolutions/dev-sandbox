#!/usr/bin/env python3
"""
Structured Logging Configuration for Fitness Influencer AI v2.0

JSON-formatted logs with request tracing, performance metrics, and Railway-compatible output.

Usage:
    from backend.logging_config import setup_logging, get_logger

    # Setup at app startup
    setup_logging()

    # Get logger for module
    logger = get_logger(__name__)
    logger.info("Processing video", extra={"video_id": "abc123", "duration": 60})
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler
from pathlib import Path
import uuid


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Output format:
    {
        "timestamp": "2026-02-07T10:30:00.123Z",
        "level": "INFO",
        "logger": "backend.main",
        "message": "Processing video",
        "request_id": "abc123",
        "user_id": "user_456",
        "endpoint": "/api/video/caption",
        "duration_ms": 2500,
        "metadata": {...}
    }
    """

    def __init__(self, include_traceback: bool = True):
        super().__init__()
        self.include_traceback = include_traceback

    def format(self, record: logging.LogRecord) -> str:
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # Add extra fields from record
        extra_fields = [
            "request_id", "user_id", "endpoint", "duration_ms",
            "status", "job_id", "job_type", "progress", "error_code"
        ]
        for field in extra_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        # Add metadata dict if present
        if hasattr(record, "metadata") and record.metadata:
            log_entry["metadata"] = record.metadata

        # Add exception info
        if record.exc_info and self.include_traceback:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add source location for errors
        if record.levelno >= logging.ERROR:
            log_entry["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }

        return json.dumps(log_entry, default=str)


class RequestContextFilter(logging.Filter):
    """
    Logging filter that adds request context to all log records.

    Context is stored in a thread-local or contextvars variable.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Add request_id if not present
        if not hasattr(record, "request_id"):
            record.request_id = getattr(RequestContext, "request_id", None)

        # Add user_id if not present
        if not hasattr(record, "user_id"):
            record.user_id = getattr(RequestContext, "user_id", None)

        # Add endpoint if not present
        if not hasattr(record, "endpoint"):
            record.endpoint = getattr(RequestContext, "endpoint", None)

        return True


class RequestContext:
    """
    Thread-safe request context for logging.

    Usage:
        RequestContext.set(request_id="abc123", user_id="user_456", endpoint="/api/video")
        logger.info("Processing")  # Automatically includes context
        RequestContext.clear()
    """

    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    start_time: Optional[float] = None

    @classmethod
    def set(
        cls,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ):
        """Set request context."""
        cls.request_id = request_id or str(uuid.uuid4())[:8]
        cls.user_id = user_id
        cls.endpoint = endpoint
        cls.start_time = datetime.utcnow().timestamp()

    @classmethod
    def clear(cls):
        """Clear request context."""
        cls.request_id = None
        cls.user_id = None
        cls.endpoint = None
        cls.start_time = None

    @classmethod
    def get_duration_ms(cls) -> Optional[int]:
        """Get request duration in milliseconds."""
        if cls.start_time:
            return int((datetime.utcnow().timestamp() - cls.start_time) * 1000)
        return None


def setup_logging(
    level: str = None,
    log_file: str = None,
    json_format: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to LOG_LEVEL env var or INFO.
        log_file: Path to log file. Defaults to logs/fitness.log if not Railway.
        json_format: Use JSON formatting (recommended for production).
        max_bytes: Max log file size before rotation.
        backup_count: Number of backup files to keep.
    """
    # Determine log level
    level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, level, logging.INFO)

    # Create logs directory
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler (always, for Railway)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)

    # File handler (if not on Railway or explicitly requested)
    is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None
    if not is_railway or log_file:
        log_file = log_file or str(logs_dir / "fitness.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Log startup
    logger = logging.getLogger("backend.logging")
    logger.info(
        "Logging configured",
        extra={
            "metadata": {
                "level": level,
                "json_format": json_format,
                "file": log_file if not is_railway else None,
                "railway": is_railway
            }
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the given module name.

    Usage:
        logger = get_logger(__name__)
        logger.info("Message", extra={"key": "value"})
    """
    return logging.getLogger(name)


# Convenience logging functions with extra fields
def log_request_start(endpoint: str, user_id: Optional[str] = None, **kwargs) -> str:
    """
    Log the start of a request and set context.

    Returns the request_id.
    """
    request_id = str(uuid.uuid4())[:8]
    RequestContext.set(request_id=request_id, user_id=user_id, endpoint=endpoint)

    logger = get_logger("backend.requests")
    logger.info(
        f"Request started: {endpoint}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "endpoint": endpoint,
            "metadata": kwargs
        }
    )
    return request_id


def log_request_end(status: str = "success", **kwargs) -> None:
    """Log the end of a request and clear context."""
    logger = get_logger("backend.requests")
    duration_ms = RequestContext.get_duration_ms()

    logger.info(
        f"Request completed: {RequestContext.endpoint}",
        extra={
            "request_id": RequestContext.request_id,
            "user_id": RequestContext.user_id,
            "endpoint": RequestContext.endpoint,
            "duration_ms": duration_ms,
            "status": status,
            "metadata": kwargs
        }
    )
    RequestContext.clear()


def log_error(message: str, error: Exception = None, **kwargs) -> None:
    """Log an error with context."""
    logger = get_logger("backend.errors")
    logger.error(
        message,
        extra={
            "request_id": RequestContext.request_id,
            "user_id": RequestContext.user_id,
            "endpoint": RequestContext.endpoint,
            "error_code": kwargs.get("error_code"),
            "metadata": kwargs
        },
        exc_info=error
    )


def log_job_event(
    job_id: str,
    event: str,
    job_type: str = None,
    progress: int = None,
    **kwargs
) -> None:
    """Log a job-related event."""
    logger = get_logger("backend.jobs")
    logger.info(
        f"Job {event}: {job_id}",
        extra={
            "job_id": job_id,
            "job_type": job_type,
            "progress": progress,
            "metadata": kwargs
        }
    )
