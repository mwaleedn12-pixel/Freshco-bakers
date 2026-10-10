import logging
import sys
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.docs_ui import get_custom_swagger_html, get_scalar_html
from app.core.portal_html import get_developer_portal_html
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.trusted_host import create_trusted_host_middleware
from app.services.errors import ServiceError

# ---------------------------------------------------------------- logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("freshco")

# ---------------------------------------------------------------- OpenAPI Metadata
OPENAPI_DESCRIPTION = """
### 🥐 Welcome to Freshco Bakers Digital Platform API

High-performance backend engine powering **Freshco Bakers** — from artisan confectionery e-commerce to multi-branch Point of Sale (POS) terminals.

#### Key Architectural Highlights:
* **Single Central Database**: Unified PostgreSQL instance powering both online storefront and physical POS counters.
* **Modern Security**: Argon2id password hashing, JWT Bearer tokens, sliding-window rate limiting, and OWASP headers.
* **Omnichannel Operations**: Unified order processing supporting Dine-in, Takeaway, and Home Delivery with real-time status progression.
* **Smart Automation**: n8n integration for instant WhatsApp order notifications.

---
* 💻 **Interactive Developer Hub**: Visit [`/dashboard`](/dashboard) for the real-time test console, telemetry, and demo controls.
* ⚡ **Scalar API Reference**: Visit [`/scalar`](/scalar) for modern interactive API documentation with multi-language code snippets.
* 📖 **Custom Swagger UI**: Visit [`/docs`](/docs) or [`/api/v1/docs`](/api/v1/docs).
"""

tags_metadata = [
    {"name": "system diagnostics", "description": "Server health, runtime metrics, system diagnostics and demo data seeding."},
    {"name": "health", "description": "Core application and database liveness probes."},
    {"name": "auth", "description": "JWT authentication, user login, registration, password hashing (Argon2id), and /me identity."},
    {"name": "categories", "description": "Bakery product categories (Breads, Celebration Cakes, French Pastries, etc.)."},
    {"name": "products", "description": "Catalog products, SKUs, pricing, barcodes, and nutritional metadata."},
    {"name": "cart", "description": "Customer shopping cart sessions, item additions, quantity management."},
    {"name": "addresses", "description": "Customer delivery addresses and geo-tagging."},
    {"name": "orders", "description": "Omnichannel order management (Dine-in, Takeaway, Online delivery) and order statuses."},
    {"name": "branches", "description": "Multi-branch bakery outlets (Gulberg Main, DHA Phase 5)."},
    {"name": "inventory", "description": "Per-branch inventory tracking, restock movements, low-stock threshold alerts."},
    {"name": "custom cakes", "description": "Custom artisanal cake builder, tiered cake requests, flavoring, quotes, and deposits."},
    {"name": "coupons", "description": "Promotional discounts, coupon validation, flat/percentage discounts."},
    {"name": "reviews", "description": "Product ratings and reviews with customer purchase verification and moderation."},
    {"name": "pos", "description": "High-throughput Point of Sale registers for branch cashiers with split tenders and instant receipts."},
    {"name": "payments", "description": "Payment verification, transaction logs, receipts, and refund requests."},
    {"name": "analytics", "description": "Executive revenue dashboards, top-selling bakery goods, sales trends."},
    {"name": "expenses", "description": "Daily operational bakery expenses, ingredient procurement, utilities, staff payroll."},
    {"name": "staff", "description": "Employee management, branch assignment, role-based access control."},
    {"name": "customers", "description": "Customer loyalty metrics, order histories, contact information."},
    {"name": "notifications", "description": "Order alerts, automated customer messaging, n8n WhatsApp webhooks."},
    {"name": "audit logs", "description": "Security audit logs recording administrative and financial actions."},
    {"name": "settings", "description": "Store configuration, tax rates, delivery fees, business operating hours."},
    {"name": "wishlist", "description": "Customer product wishlists and favorites."},
]

# ---------------------------------------------------------------- app
app = FastAPI(
    title=f"{settings.APP_NAME} — Digital Management Platform",
    summary="Enterprise backend engine for Freshco Bakers artisan confectionery & multi-branch network.",
    description=OPENAPI_DESCRIPTION,
    version="1.0.0",
    openapi_tags=tags_metadata,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=None,  # Handled with custom dark-gold bakery theme below
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# ---------------------------------------------------------------- middleware
# Order matters — outermost middleware runs first:
#   1. Request-ID     (assigns trace id before anything else)
#   2. Trusted Host   (rejects bad Host headers early)
#   3. Security Hdrs  (adds OWASP headers to every response)
#   4. Rate Limit     (blocks abusive IPs)
#   5. CORS           (browser preflight handling)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id", "X-RateLimit-Limit"],
)

# Trusted-host is Starlette-native (wraps the ASGI app)
if settings.ENVIRONMENT == "production":
    app = create_trusted_host_middleware(app)

# ---------------------------------------------------------------- error handler
@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    logger.warning("ServiceError [%s]: %s", exc.status_code, exc.message)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# ---------------------------------------------------------------- UI & Docs Routes
@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
@app.get("/portal", response_class=HTMLResponse, include_in_schema=False)
def developer_portal() -> HTMLResponse:
    """Developer & Operations Control Hub."""
    return HTMLResponse(get_developer_portal_html(
        app_name=settings.APP_NAME,
        version="1.0.0",
        env=settings.ENVIRONMENT,
    ))


@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
@app.get(f"{settings.API_V1_PREFIX}/docs", response_class=HTMLResponse, include_in_schema=False)
def custom_swagger_docs() -> HTMLResponse:
    """Custom-styled Freshco Bakers Swagger UI."""
    return HTMLResponse(get_custom_swagger_html(
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        title=f"{settings.APP_NAME} API — Swagger UI",
    ))


@app.get("/scalar", response_class=HTMLResponse, include_in_schema=False)
def scalar_reference() -> HTMLResponse:
    """Modern Scalar API Reference."""
    return HTMLResponse(get_scalar_html(
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        title=f"{settings.APP_NAME} API Reference — Scalar",
    ))


@app.get("/swagger", include_in_schema=False)
def redirect_swagger() -> RedirectResponse:
    return RedirectResponse(url=f"{settings.API_V1_PREFIX}/docs")


@app.get("/redoc", include_in_schema=False)
def redirect_redoc() -> RedirectResponse:
    return RedirectResponse(url=f"{settings.API_V1_PREFIX}/redoc")


# ---------------------------------------------------------------- API Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", summary="Root & Platform Entry Point")
def root(request: Request) -> Any:
    accept = request.headers.get("accept", "")
    # When navigated directly in a browser expecting HTML, show the control hub:
    if "text/html" in accept and not accept.startswith("*/*"):
        return HTMLResponse(get_developer_portal_html(
            app_name=settings.APP_NAME,
            version="1.0.0",
            env=settings.ENVIRONMENT,
        ))

    # Standard JSON for test suites, API clients & automated tooling:
    return {
        "message": f"{settings.APP_NAME} API is running",
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/api/v1/docs",
        "scalar_url": "/scalar",
        "dashboard_url": "/dashboard",
    }
