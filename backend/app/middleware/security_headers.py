"""
Security-headers middleware.

Adds OWASP-recommended HTTP security headers to every response:

  - Strict-Transport-Security (HSTS)
  - X-Content-Type-Options
  - X-Frame-Options
  - X-XSS-Protection (legacy browsers)
  - Referrer-Policy
  - Permissions-Policy
  - Content-Security-Policy (report-only in dev, enforced in production)

These headers are always added regardless of route, so the frontend
(static HTML) and the API both benefit.
"""
from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects security headers into every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.is_production = settings.ENVIRONMENT == "production"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # HSTS — tell browsers to always use HTTPS (only meaningful in prod behind TLS)
        if self.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS filter (modern browsers use CSP, but this doesn't hurt)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer leak prevention
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(self)"
        )

        # Content-Security-Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' http://localhost:8000 https://api.freshcobakers.com; "
            "frame-ancestors 'none';"
        )
        if self.is_production:
            response.headers["Content-Security-Policy"] = csp
        else:
            # Report-only in dev so it doesn't break anything while developing
            response.headers["Content-Security-Policy-Report-Only"] = csp

        return response
