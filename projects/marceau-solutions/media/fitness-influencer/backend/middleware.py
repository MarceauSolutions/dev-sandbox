#!/usr/bin/env python3
"""
FastAPI Middleware for Fitness Influencer AI v2.0

Request tracing, logging, and performance monitoring middleware.

Usage:
    from backend.middleware import setup_middleware

    app = FastAPI()
    setup_middleware(app)
"""

import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.logging_config import (
    RequestContext,
    get_logger,
    log_request_start,
    log_request_end
)

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all requests with timing and context.

    Adds:
    - Unique request_id to each request
    - Request/response logging
    - Performance timing
    - Error tracking
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for health checks and static files
        skip_paths = ["/", "/health", "/static/", "/favicon.ico"]
        if any(request.url.path.startswith(p) for p in skip_paths if p != "/"):
            return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())[:8]

        # Extract user_id from headers or auth (if available)
        user_id = request.headers.get("X-User-ID")

        # Set context for all logs during this request
        RequestContext.set(
            request_id=request_id,
            user_id=user_id,
            endpoint=request.url.path
        )

        # Add request_id to request state for access in endpoints
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Log request start
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "endpoint": request.url.path,
                "metadata": {
                    "method": request.method,
                    "query_params": str(request.query_params),
                    "client_host": request.client.host if request.client else None
                }
            }
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Add timing headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"

            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} {response.status_code}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "endpoint": request.url.path,
                    "duration_ms": duration_ms,
                    "status": "success" if response.status_code < 400 else "error",
                    "metadata": {
                        "status_code": response.status_code,
                        "method": request.method
                    }
                }
            )

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "endpoint": request.url.path,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "metadata": {
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                },
                exc_info=True
            )
            raise

        finally:
            # Clear context
            RequestContext.clear()


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking performance metrics.

    Tracks:
    - Request counts by endpoint
    - Response times
    - Error rates
    """

    def __init__(self, app, metrics_collector=None):
        super().__init__(app)
        self.metrics = metrics_collector or InMemoryMetrics()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        endpoint = request.url.path
        method = request.method

        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record successful request
            self.metrics.record_request(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                duration=duration
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Record failed request
            self.metrics.record_request(
                endpoint=endpoint,
                method=method,
                status_code=500,
                duration=duration,
                error=str(e)
            )
            raise


class InMemoryMetrics:
    """Simple in-memory metrics collector."""

    def __init__(self):
        self.requests = []
        self.max_entries = 10000

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        error: str = None
    ):
        """Record a request metric."""
        entry = {
            "timestamp": time.time(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": int(duration * 1000),
            "error": error
        }
        self.requests.append(entry)

        # Trim old entries
        if len(self.requests) > self.max_entries:
            self.requests = self.requests[-self.max_entries:]

    def get_stats(self, minutes: int = 5) -> dict:
        """Get request statistics for the last N minutes."""
        cutoff = time.time() - (minutes * 60)
        recent = [r for r in self.requests if r["timestamp"] > cutoff]

        if not recent:
            return {"total": 0, "error_rate": 0, "avg_duration_ms": 0}

        total = len(recent)
        errors = len([r for r in recent if r["status_code"] >= 400])
        avg_duration = sum(r["duration_ms"] for r in recent) / total

        return {
            "total": total,
            "error_rate": errors / total if total > 0 else 0,
            "avg_duration_ms": int(avg_duration),
            "errors": errors
        }


# Global metrics instance
_metrics = InMemoryMetrics()


def get_metrics() -> InMemoryMetrics:
    """Get the global metrics instance."""
    return _metrics


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the application.

    Call this after creating the FastAPI app.
    """
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(PerformanceMonitoringMiddleware, metrics_collector=_metrics)
    app.add_middleware(RequestLoggingMiddleware)

    logger.info("Middleware configured")
