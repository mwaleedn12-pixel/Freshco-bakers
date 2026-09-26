# Module 01 — Project Scaffolding + Freshco Bakers Branding + 3D UI

**Status:** ✅ Ready to push
**Date:** 2026-09-26

## What this module does
- Full monorepo scaffold: FastAPI backend + Flutter frontend + docs, per the SRS.
- Backend: config, Argon2id security helpers, DB session/engine, Alembic wiring, `/health` and `/health/db` endpoints. Verified with `pytest` (2/2 passing).
- Frontend: routing (go_router), theming, API client (Dio) skeleton, and empty feature folders for every module to come (auth, catalog, cart, checkout, orders, custom_cake, reviews, customer, admin, pos).
- Branding: renamed everything from generic "Bakery Platform" to **Freshco Bakers** (Flutter package name, app title, backend APP_NAME, default DB name).
- **3D UI:** new reusable `Tilt3DCard` widget (`frontend/lib/shared/widgets/tilt_3d_card.dart`) using Flutter `Matrix4` perspective transforms — cards tilt toward the pointer/drag with dynamic shadows. Applied to the home screen's hero "Order Now" button and 4 featured-product cards.

## Files added
```
freshco-bakers/.gitignore
freshco-bakers/README.md
freshco-bakers/backend/.env.example
freshco-bakers/backend/alembic.ini
freshco-bakers/backend/requirements.txt
freshco-bakers/backend/app/main.py
freshco-bakers/backend/app/core/config.py
freshco-bakers/backend/app/core/security.py
freshco-bakers/backend/app/db/base.py
freshco-bakers/backend/app/db/session.py
freshco-bakers/backend/app/api/v1/__init__.py
freshco-bakers/backend/app/api/v1/endpoints/health.py
freshco-bakers/backend/migrations/env.py
freshco-bakers/backend/migrations/script.py.mako
freshco-bakers/backend/tests/test_health.py
freshco-bakers/docs/SRS_Architecture.pdf
freshco-bakers/frontend/pubspec.yaml
freshco-bakers/frontend/lib/main.dart
freshco-bakers/frontend/lib/core/theme/app_theme.dart
freshco-bakers/frontend/lib/core/routing/app_router.dart
freshco-bakers/frontend/lib/core/network/api_client.dart
freshco-bakers/frontend/lib/features/home/home_screen.dart
freshco-bakers/frontend/lib/shared/widgets/tilt_3d_card.dart
(+ empty __init__.py / .gitkeep placeholders in every module folder)
```

## Git commit used
```
Module 1: Freshco Bakers scaffolding + 3D UI
```

## Next module
**Module 2 — Database Models** (users, roles, products, categories, orders, inventory — SQLAlchemy models + first Alembic migration).
