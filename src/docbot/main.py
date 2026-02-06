"""DocBot FastAPI application with health endpoints and logging middleware."""

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: setup config and logging on startup."""
    # Import here to allow proper initialization order
    from docbot.config import get_settings
    from docbot.logging_config import setup_logging
    from docbot.database import init_db

    # Load configuration
    settings = get_settings()

    # Setup structured logging
    setup_logging(settings.app.log_level)

    import logging
    logger = logging.getLogger(__name__)
    logger.info("DocBot API starting up", extra={"env": settings.app.env})

    # Initialize database schema (safe to run multiple times)
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    yield

    logger.info("DocBot API shutting down")


app = FastAPI(
    title="DocBot API",
    version="0.1.0",
    lifespan=lifespan
)

# Configure Jinja2 templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files directory
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Add SessionMiddleware for authentication
from docbot.config import get_settings
settings = get_settings()
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.auth.session_secret_key or "dev-secret-key-change-in-prod",
    session_cookie="docbot_session",
    max_age=None,
    https_only=(settings.app.env == "prod"),
    same_site="lax"
)

# Include auth router
from docbot import auth
app.include_router(auth.router)

# Include webhook router
from docbot import webhook
app.include_router(webhook.router)


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
    from docbot.database import get_db

    # Check config loaded successfully
    try:
        settings = get_settings()
        config_ready = True
    except Exception:
        config_ready = False

    # Check database connectivity
    database_ready = False
    try:
        async for db in get_db():
            result = await db.execute("SELECT 1")
            await result.fetchone()
            database_ready = True
            break
    except Exception:
        pass

    return {
        "status": "ready",
        "checks": {
            "config": config_ready,
            "database": database_ready
        }
    }


@app.get("/")
async def landing_page(request: Request):
    """
    Landing page - shows login if not authenticated, redirects to dashboard if authenticated.
    """
    user = request.session.get('user')

    if user:
        # User is already logged in, redirect to dashboard
        return RedirectResponse(url="/dashboard")

    # Show login page
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/auth/error")
async def auth_error_page(request: Request):
    """
    Display authentication error page with retry option.
    """
    error_message = request.query_params.get("message", "An error occurred during authentication.")
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error_message": error_message}
    )


@app.get("/dashboard")
async def dashboard(request: Request):
    """
    Protected dashboard route - placeholder until React frontend in Phase 4.

    Returns JSON with user info. Will be replaced by React app later.
    Redirects to login page if not authenticated.
    """
    user = request.session.get('user')

    if not user:
        # Redirect to landing page for GET requests
        return RedirectResponse(url="/", status_code=307)

    return {
        "message": "Dashboard coming in Phase 4",
        "user": user.get("email") if isinstance(user, dict) else None
    }
