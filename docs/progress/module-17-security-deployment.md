# Module 17 — Security Hardening & Deployment

Pushed / Built status: 📦 Complete & Ready for Push

## 1. Features Delivered

### Security Middleware Stack
- **Rate Limiting** (`app/middleware/rate_limit.py`):
  - Sliding-window per-IP counter (120 req/min default, configurable).
  - Exempt paths for docs/health endpoints.
  - `X-RateLimit-Limit` response header on every request.
  - `Retry-After` header on 429 responses.
  - X-Forwarded-For–aware for reverse-proxy setups.

- **Security Headers** (`app/middleware/security_headers.py`):
  - HSTS (production only, 2-year max-age with preload).
  - X-Content-Type-Options: nosniff.
  - X-Frame-Options: DENY.
  - X-XSS-Protection: 1; mode=block.
  - Referrer-Policy: strict-origin-when-cross-origin.
  - Permissions-Policy (camera, mic, geo blocked; payment=self).
  - Content-Security-Policy (report-only in dev, enforced in production).

- **Request-ID Tracing** (`app/middleware/request_id.py`):
  - UUID4 auto-generated per request, or echoes client-supplied X-Request-Id.
  - Available in `request.state.request_id` for logging.
  - Returned in X-Request-Id response header.

- **Trusted Host Validation** (`app/middleware/trusted_host.py`):
  - Blocks requests with invalid Host headers in production.
  - Uses Starlette built-in TrustedHostMiddleware.

### Production Configuration
- `config.py` extended with `RATE_LIMIT_*`, `ALLOWED_HOSTS`, `LOG_LEVEL` settings.
- `.env.example` updated with all new keys.
- Structured logging (timestamped, leveled) added to `main.py`.

### Docker Setup
- **Multi-stage Dockerfile** (`backend/Dockerfile`):
  - Builder stage compiles native deps (argon2, psycopg).
  - Slim runtime image with non-root user.
  - Built-in health check.
  - 4-worker uvicorn with proxy-headers support.

- **docker-compose.yml** (root):
  - PostgreSQL 16 with health check and persistent volume.
  - Redis 7 with health check.
  - Backend with all env vars and dependency ordering.
  - Nginx reverse proxy serving frontend static files + API proxy.

### Nginx Reverse Proxy
- **nginx/nginx.conf**:
  - HTTP → HTTPS redirect.
  - TLS 1.2/1.3 with modern cipher suite.
  - HSTS preload.
  - Gzip compression for text/JS/CSS/JSON.
  - Static asset caching (30 days, immutable).
  - API rate limiting zones (30 req/s general, 5 req/min for auth).
  - Request-ID propagation to backend.
  - Optional api.freshcobakers.com subdomain.

### CI/CD Pipeline
- **`.github/workflows/ci.yml`**:
  - Lint job (ruff check + format).
  - Test job (pytest with pip caching).
  - Docker build verification.
  - Tagged release → publish image to GitHub Container Registry.

## 2. Key Files Added/Modified
- `backend/app/middleware/__init__.py` (new)
- `backend/app/middleware/rate_limit.py` (new)
- `backend/app/middleware/security_headers.py` (new)
- `backend/app/middleware/request_id.py` (new)
- `backend/app/middleware/trusted_host.py` (new)
- `backend/app/core/config.py` (modified — new settings)
- `backend/app/main.py` (modified — middleware integration, logging, v1.0.0)
- `backend/.env.example` (modified — new keys)
- `backend/Dockerfile` (new)
- `backend/.dockerignore` (new)
- `backend/tests/test_module_17.py` (new)
- `docker-compose.yml` (new)
- `nginx/nginx.conf` (new)
- `nginx/certs/README.md` (new)
- `.github/workflows/ci.yml` (new)
