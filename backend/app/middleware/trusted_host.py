"""
Trusted-host validation middleware.

Rejects requests whose ``Host`` header doesn't match one of the configured
ALLOWED_HOSTS. Prevents host-header-injection attacks and DNS rebinding.

In development mode (ENVIRONMENT != production) it is permissive; any host
is allowed (localhost, 127.0.0.1, etc.).
"""
from __future__ import annotations

from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


def create_trusted_host_middleware(app: ASGIApp) -> TrustedHostMiddleware:
    """Factory — returns the built-in Starlette TrustedHostMiddleware
    configured from settings."""
    allowed = getattr(settings, "ALLOWED_HOSTS", ["*"])
    if settings.ENVIRONMENT != "production":
        allowed = ["*"]
    return TrustedHostMiddleware(app, allowed_hosts=allowed)
