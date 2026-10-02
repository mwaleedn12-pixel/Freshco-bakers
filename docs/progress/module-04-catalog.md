# Module 04 — Products & Categories API

**Status:** ✅ Ready to push
**Date:** 2026-09-28
**Delivered together with:** Module 05

## What this module does
- **Public (no login):** `GET /categories`, `GET /categories/{id}`, `GET /products` (search, category incl.
  sub-categories, featured, pagination), `GET /products/{id}`. Only *active* items are shown and
  `cost_price` is never exposed.
- **Admin/Owner only:** create/update/delete categories; create/update/archive products; add/remove
  product images (URL based — file upload comes later); `GET /categories/admin/list` and
  `GET /products/admin/list` show everything including inactive/archived items and cost price.
- **Delete = archive** for products (status `archived`, `is_available=false`) so old orders and history stay intact.
  Categories can only be deleted when empty.
- **Rules enforced:** unique SKU/barcode (409), sale price must be lower than price, category must exist,
  slugs are generated and made unique automatically.
- **Audit logs:** every admin change writes a row to `audit_logs` (who, action, old data, new data).
- **`python -m app.scripts.create_admin`** — creates the 5 roles (customer, cashier, manager, admin, owner) and
  an owner/admin user. Needed once, otherwise nobody can use the admin endpoints.
- **`ServiceError`** + global handler in `main.py` — services raise clean business errors that become JSON responses.

## Bug fixed on the way
`uvicorn app.main:app` could crash with a circular import (models <-> db/base). Fixed in `app/models/__init__.py`;
verified for every import order.

## Files added / changed
```
backend/app/main.py                          (replaced — error handler)
backend/app/models/__init__.py               (replaced — circular import fix)
backend/app/api/v1/__init__.py               (replaced — registers new routers)
backend/app/api/v1/endpoints/categories.py   (new)
backend/app/api/v1/endpoints/products.py     (new)
backend/app/schemas/catalog.py               (new)
backend/app/services/catalog_service.py      (new)
backend/app/services/audit_service.py        (new)
backend/app/services/errors.py               (new)
backend/app/utils/slug.py                    (new)
backend/app/scripts/__init__.py              (new)
backend/app/scripts/create_admin.py          (new)
backend/tests/conftest.py                    (new — fresh in-memory DB per test, auth_headers helper)
backend/tests/test_catalog.py                (new)
```

## Git commit used
```
Module 4: products & categories API (admin CRUD, public catalog, audit logs, create_admin script)
```
