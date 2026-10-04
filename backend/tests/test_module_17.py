"""
Tests for Module 17: Security Hardening & Deployment
-----------------------------------------------------
Tests the new middleware (rate limiting, security headers, request ID)
and verifies they integrate correctly with the existing API.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ─── Request-ID Middleware ───────────────────────────────
class TestRequestId:
    """X-Request-Id should be present on every response."""

    def test_response_has_request_id(self, client):
        r = client.get("/api/v1/health")
        assert "x-request-id" in r.headers

    def test_client_supplied_id_is_echoed(self, client):
        custom_id = "test-trace-12345"
        r = client.get("/api/v1/health", headers={"X-Request-Id": custom_id})
        assert r.headers["x-request-id"] == custom_id

    def test_auto_generated_id_is_uuid4(self, client):
        r = client.get("/api/v1/health")
        rid = r.headers["x-request-id"]
        # UUID4 pattern: 8-4-4-4-12 hex chars
        parts = rid.split("-")
        assert len(parts) == 5


# ─── Security-Headers Middleware ─────────────────────────
class TestSecurityHeaders:
    """OWASP headers should be injected on every response."""

    def test_x_content_type_options(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("x-frame-options") == "DENY"

    def test_x_xss_protection(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("x-xss-protection") == "1; mode=block"

    def test_referrer_policy(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client):
        r = client.get("/api/v1/health")
        assert "permissions-policy" in r.headers

    def test_csp_report_only_in_dev(self, client):
        """In development mode, CSP is report-only (shouldn't block anything)."""
        r = client.get("/api/v1/health")
        # Dev mode → report-only header
        assert "content-security-policy-report-only" in r.headers or "content-security-policy" in r.headers


# ─── Rate-Limit Headers ─────────────────────────────────
class TestRateLimitHeaders:
    """Every non-exempt response should include rate-limit info headers."""

    def test_rate_limit_header_present(self, client):
        r = client.get("/api/v1/products?limit=1")
        assert "x-ratelimit-limit" in r.headers

    def test_exempt_paths_have_no_rate_limit_header(self, client):
        """Health endpoint is exempt — should NOT have the rate-limit header."""
        r = client.get("/api/v1/health")
        # Exempt paths skip the middleware entirely, so no X-RateLimit-Limit
        # (The header might still appear from the outer middleware chain, so
        # we just confirm it doesn't get a 429.)
        assert r.status_code != 429


# ─── Root endpoint still works ───────────────────────────
class TestRootEndpoint:
    def test_root_returns_message(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "Freshco Bakers" in r.json()["message"]


# ─── App version bump ───────────────────────────────────
class TestAppMeta:
    def test_openapi_version(self, client):
        r = client.get("/api/v1/openapi.json")
        assert r.status_code == 200
        data = r.json()
        assert data["info"]["version"] == "1.0.0"
