"""DocBot FastAPI application with health endpoints and logging middleware."""

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: setup config and logging on startup."""
    # Import here to allow proper initialization order
    from docbot.config import get_settings
    from docbot.logging_config import setup_logging

    # Load configuration
    settings = get_settings()

    # Setup structured logging
    setup_logging(settings.app.log_level)

    import logging
    logger = logging.getLogger(__name__)
    logger.info("DocBot API starting up", extra={"env": settings.app.env})

    yield

    logger.info("DocBot API shutting down")


app = FastAPI(
    title="DocBot API",
    version="0.1.0",
    lifespan=lifespan
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every HTTP request with structured JSON including request_id, method, path, status, duration."""
    import logging
    from docbot.logging_config import request_id_var

    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)

    logger = logging.getLogger("docbot.http")

    start_time = time.time()

    # Process request
    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000

    # Log request details
    logger.info(
        "HTTP request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
    )

    return response


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint - returns liveness status."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """Readiness check endpoint - returns readiness when dependencies are available."""
    from docbot.config import get_settings

    # Check config loaded successfully
    try:
        settings = get_settings()
        config_ready = True
    except Exception:
        config_ready = False

    # Will add database check in Plan 02

    return {
        "status": "ready",
        "checks": {
            "config": config_ready
        }
    }
