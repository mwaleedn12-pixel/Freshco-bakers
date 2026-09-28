# Module 03 — Auth (Register, Login, JWT, Role Protection)

**Status:** ✅ Ready to push
**Date:** 2026-09-26

## What this module does
- **POST /api/v1/auth/register** — creates a user, auto-creates the `customer` role if it
  doesn't exist yet (no manual seeding needed for a fresh DB), hashes the password with
  Argon2id, returns a JWT + user profile.
- **POST /api/v1/auth/login** — verifies email/password, returns a fresh JWT + user profile.
- **GET /api/v1/auth/me** — returns the current user's profile from the `Authorization: Bearer <token>` header.
- **`app/core/deps.py`** — `get_current_user` (decodes JWT, loads the user) and
  `require_roles('admin', 'owner', ...)` — a reusable dependency every future protected
  endpoint (products, orders, POS, admin) will use for role-based access control.
- Verified with `tests/test_auth.py`: register → duplicate-email rejected (400) → login →
  wrong password rejected (401) → `/me` with valid token (200) → `/me` with no token rejected (401).
- Full suite: **4/4 tests passing** (2 from Module 1, 1 from Module 2, this one).

## New dependency
Added `email-validator==2.2.0` to `requirements.txt` (required by Pydantic's `EmailStr` — was missing,
caught immediately by the test suite).

## Files added / changed
```
backend/requirements.txt                    (changed — added email-validator)
backend/app/schemas/auth.py                 (new)
backend/app/services/auth_service.py        (new)
backend/app/core/deps.py                    (new)
backend/app/api/v1/endpoints/auth.py        (new)
backend/app/api/v1/__init__.py              (replaced — registers the /auth router)
backend/tests/test_auth.py                  (new)
```

## How to use this from here on (for future modules)
Any endpoint that should require login:
```python
from app.core.deps import get_current_user
current_user: User = Depends(get_current_user)
```

Any endpoint that should require a specific role (e.g. only admin/owner can delete a product):
```python
from app.core.deps import require_roles
current_user: User = Depends(require_roles("admin", "owner"))
```

## Try it yourself (once your local server is running)
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Ali Raza","email":"ali@example.com","password":"supersecret123"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ali@example.com","password":"supersecret123"}'

curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <paste-token-here>"
```
Or just open http://localhost:8000/api/v1/docs and try it from Swagger UI.

## Git commit used
```
Module 3: auth (register, login, JWT, role-based access control)
```

## Next module
**Module 4 — Products & Categories API** (admin CRUD for categories/products/images,
public GET endpoints for the customer-facing catalog, protected with `require_roles("admin", "owner")`
for write operations).
