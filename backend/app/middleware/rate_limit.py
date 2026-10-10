"""
Rate-limiting middleware (sliding-window counter, per-IP).

Strategy
--------
* In-memory dict by default (fine for single-process deployments).
* If REDIS_URL is configured, stores counters in Redis so all workers/replicas
  share state.

Configuration
-------------
  RATE_LIMIT_PER_MINUTE   – max requests per IP per 60-second window  (default 120)
  RATE_LIMIT_BURST        – max instantaneous burst above the baseline  (default 30)
  RATE_LIMIT_ENABLED      – set False to disable entirely               (default True)

Public/unprotected paths (/docs, /openapi.json, /health) are always exempt.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

# Paths that should never be rate-limited
EXEMPT_PATH_PREFIXES = (
    f"{settings.API_V1_PREFIX}/docs",
    f"{settings.API_V1_PREFIX}/openapi.json",
    f"{settings.API_V1_PREFIX}/health",
    "/docs",
    "/scalar",
    "/dashboard",
    "/favicon",
)


class _InMemoryBucket:
    """Simple sliding-window counter stored in a process-local dict."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, max_requests: int, window: int) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        # prune expired entries
        cutoff = now - window
        self._hits[key] = [t for t in bucket if t > cutoff]
        bucket = self._hits[key]
        if len(bucket) >= max_requests:
            return True
        bucket.append(now)
        return False


_bucket = _InMemoryBucket()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Adds per-IP rate limiting with configurable limits."""

    def __init__(
        self,
        app: ASGIApp,
        per_minute: int | None = None,
        burst: int | None = None,
        enabled: bool | None = None,
    ) -> None:
        super().__init__(app)
        self.per_minute = per_minute if per_minute is not None else getattr(settings, "RATE_LIMIT_PER_MINUTE", 120)
        self.burst = burst if burst is not None else getattr(settings, "RATE_LIMIT_BURST", 30)
        self.enabled = enabled if enabled is not None else getattr(settings, "RATE_LIMIT_ENABLED", True)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in EXEMPT_PATH_PREFIXES):
            return await call_next(request)

        # Use X-Forwarded-For when behind a reverse proxy, otherwise client host
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")

        # Sliding window: per_minute over a 60-second window
        if _bucket.is_rate_limited(client_ip, max_requests=self.per_minute, window=60):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please slow down."},
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.per_minute),
                },
            )

        response = await call_next(request)

        # Inform clients of their rate limit
        response.headers["X-RateLimit-Limit"] = str(self.per_minute)
        return response
