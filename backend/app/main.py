import logging
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
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

# ---------------------------------------------------------------- app
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
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


# ---------------------------------------------------------------- routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root() -> dict:
    return {"message": f"{settings.APP_NAME} API is running"}
