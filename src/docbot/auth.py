"""Google OAuth authentication with session management."""

import logging
from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from docbot.config import get_settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth client configuration
oauth = OAuth()


def configure_oauth():
    """Configure OAuth client with Google provider."""
    settings = get_settings()

    oauth.register(
        name='google',
        client_id=settings.auth.google_client_id,
        client_secret=settings.auth.google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    logger.info("OAuth client configured for Google")


def get_session_middleware() -> SessionMiddleware:
    """
    Factory function to create SessionMiddleware instance.

    Returns a configured SessionMiddleware with:
    - Secret key from settings
    - httponly=True (prevents JavaScript access)
    - samesite="lax" (CSRF protection while allowing top-level navigation)
    - secure=True in production (HTTPS only)
    - max_age=None (session persists indefinitely per AUTH-02)

    Called by main.py during app setup.
    """
    settings = get_settings()

    # Determine if we're in production (use secure cookies)
    is_production = settings.app.env == "prod"

    middleware = SessionMiddleware(
        app=None,  # Will be set by FastAPI when middleware is added
        secret_key=settings.auth.session_secret_key,
        session_cookie="docbot_session",
        max_age=None,  # Never expires - AUTH-02
        https_only=is_production,  # Secure cookies in production
        same_site="lax",
    )

    logger.info(
        "SessionMiddleware configured",
        extra={
            "secure": is_production,
            "max_age": None,
            "same_site": "lax"
        }
    )

    return middleware


@router.get("/login")
async def login(request: Request):
    """
    Initiate Google OAuth login flow.

    Redirects user to Google OAuth authorization URL.
    """
    try:
        settings = get_settings()
        redirect_uri = f"{settings.app.base_url}/auth/callback"

        logger.info(
            "Initiating OAuth login",
            extra={"redirect_uri": redirect_uri}
        )

        # Configure OAuth if not already done
        if 'google' not in oauth._clients:
            configure_oauth()

        return await oauth.google.authorize_redirect(request, redirect_uri)

    except Exception as e:
        logger.error(
            "OAuth login initiation failed",
            extra={"error": str(e)},
            exc_info=True
        )
        return RedirectResponse(url="/auth/error?message=Failed to initiate login")


@router.get("/callback")
async def callback(request: Request):
    """
    Handle OAuth callback from Google.

    Extracts user info (email, name, picture) and stores in session.
    Redirects to dashboard on success, error page on failure.
    """
    try:
        # Configure OAuth if not already done
        if 'google' not in oauth._clients:
            configure_oauth()

        # Exchange authorization code for token
        token = await oauth.google.authorize_access_token(request)

        # Get user info from token
        user_info = token.get('userinfo')
        if not user_info:
            raise ValueError("No user info in token")

        # Extract user details
        user_data = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
        }

        # Store in session (AUTH-02: persistent session)
        request.session['user'] = user_data

        logger.info(
            "OAuth login successful",
            extra={"user_email": user_data['email']}
        )

        # Redirect to dashboard (or / for now)
        return RedirectResponse(url="/dashboard")

    except Exception as e:
        logger.error(
            "OAuth callback failed",
            extra={"error": str(e)},
            exc_info=True
        )
        return RedirectResponse(url="/auth/error?message=Authentication failed")


@router.get("/logout")
async def logout(request: Request):
    """
    Clear user session and redirect to landing page.
    """
    # Clear session
    request.session.clear()

    logger.info("User logged out")

    return RedirectResponse(url="/")


@router.get("/error")
async def error(request: Request):
    """
    Display error page (rendered by main.py template).

    This route exists to be referenced in redirects, but the actual
    rendering is handled by main.py's error template route.
    """
    # This will be handled by main.py template rendering
    pass


async def require_auth(request: Request) -> dict[str, Any]:
    """
    FastAPI dependency that checks for authenticated session.

    Returns user dict if authenticated, otherwise redirects to landing page
    for GET requests or returns 401 for API requests.

    AUTH-03: No allowlist check - any Google account works.

    Usage:
        @app.get("/dashboard")
        async def dashboard(user: dict = Depends(require_auth)):
            return {"user": user}

    Returns:
        dict: User data with email, name, picture
    """
    user = request.session.get('user')

    if not user:
        logger.warning(
            "Unauthenticated access attempt",
            extra={"path": request.url.path, "method": request.method}
        )

        # Redirect to landing page for GET requests
        if request.method == "GET":
            return RedirectResponse(url="/", status_code=307)
        else:
            # Return 401 for API requests
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Not authenticated")

    # AUTH-03: No allowlist check - any Google account accepted
    return user
