"""
Request-ID middleware.

Assigns a unique identifier to every incoming request and returns it in the
``X-Request-Id`` response header. If the client already sent an
``X-Request-Id`` header (common behind API gateways), the server re-uses it.

This makes it trivial to correlate logs, errors, and support tickets to a
specific API call.
"""
from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Adds / propagates X-Request-Id on every request/response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Reuse if upstream proxy already set one, otherwise generate
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

        # Make it available to downstream handlers via request.state
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
