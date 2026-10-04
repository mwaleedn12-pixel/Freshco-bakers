# Freshco Bakers — Module Tracker

Updated: 2026-10-04 · Backend tests: **29+ passing** · Repo: https://github.com/mwaleedn12-pixel/Freshco-bakers

Legend: ✅ pushed to GitHub · 📦 built & tested, ready for push · ⏳ not started

---

## ✅ / 📦 Done modules

| # | Module | Status | What you get | Details file |
|---|--------|--------|--------------|--------------|
| 1 | Scaffolding + Freshco branding + 3D UI | ✅ pushed | Monorepo, FastAPI skeleton, Flutter skeleton, brand theme, 3D tilt cards on home screen | `module-01-scaffolding-branding-3d-ui.md` |
| 2 | Database models | ✅ pushed | 28 tables from the SRS (users, catalog, orders, inventory, coupons, audit logs...) | `module-02-database-models.md` |
| 3 | Auth | ✅ pushed | Register, login (JWT), `/auth/me`, Argon2id passwords, role-based access (`require_roles`) | `module-03-auth.md` |
| 4 | Products & Categories API | ✅ pushed | Public catalog + search, admin CRUD, images, archive, audit logs, `create_admin` script | `module-04-catalog.md` |
| 5 | Cart, Addresses, Checkout & Orders | ✅ pushed | Cart, addresses, checkout with server-side prices, coupon, tax, delivery fee, stock reservation, cancel | `module-05-cart-orders.md` |
| 6 | Branches & Inventory | ✅ pushed | Branch management, stock in/out/waste/adjust/transfer, low-stock alerts, transaction history | `module-06-branches-inventory.md` |
| 7 | Admin Orders Workflow & Notifications | ✅ pushed | Staff order list/filters, status flow, stock deduction on completion, payment marking, in-app notifications | `module-07-admin-orders-notifications.md` |
| 8 | Coupons Admin, Custom Cakes & Reviews | ✅ pushed | Coupon CRUD + validate, custom cake request→quote→accept→done, reviews with moderation + ratings | `module-08-coupons-cakes-reviews.md` |
| 9 | Staff, Customers & Settings API | ✅ pushed | Staff CRUD, role permissions, customer analytics & lifetime spend, bakery key-value settings, profile update | `module-09-staff-customers-settings.md` |
| 10 | Payments, Receipts & Email | ✅ pushed | Payment processing (Cash/Card/Online/Wallet), 58mm/80mm thermal receipt generator, notification stubs | `module-10-to-13-payments-analytics-pos-expenses.md` |
| 11 | Dashboard, Analytics & Reports API | ✅ pushed | Revenue, AOV, order source breakdown (Website vs POS vs WhatsApp), gross profit analytics | `module-10-to-13-payments-analytics-pos-expenses.md` |
| 12 | POS backend (Phase 2) | ✅ pushed | Direct POS sale on central orders table, barcode lookup, cash/card receipt, returns & daily closing | `module-10-to-13-payments-analytics-pos-expenses.md` |
| 13 | Expenses, Returns & Profit | ✅ pushed | Branch operating expenses, net profit calculator (Revenue − COGS − Expenses), audit log viewer | `module-10-to-13-payments-analytics-pos-expenses.md` |
| 14 | Flutter / Web Customer App | ✅ pushed | Auth, 3D interactive home screen, catalog + search, cart, checkout, orders tracking, custom cake request form, reviews | `module-14-to-16-frontend.md` |
| 15 | Flutter / Web Admin Dashboard | ✅ pushed | Executive dashboard, product management, order kanban board, inventory management, custom cake quotes, coupons, reviews moderation, staff, reports, settings | `module-14-to-16-frontend.md` |
| 16 | Flutter / Web POS Counter Billing | ✅ pushed | Search / barcode scan, fast counter billing, payment popup, thermal print receipt preview (58mm/80mm), POS returns, daily closing | `module-14-to-16-frontend.md` |
| 17 | Security Hardening & Deployment | 📦 ready | Rate limiting, security headers (HSTS/CSP/XSS), request-ID tracing, trusted-host validation, Dockerfile, docker-compose, Nginx reverse proxy, GitHub Actions CI/CD | `module-17-security-deployment.md` |

---

## ✅ All modules complete!

**Commit message for Module 17 push:**
```
Module 17: Security hardening & deployment — rate limiting, OWASP headers, Docker, Nginx, CI/CD
```

---

## Technical to-dos (not modules, but needed before going live)

- [ ] Install PostgreSQL locally and create the database (`freshco_bakers_db`) — the live server needs it; tests use SQLite and don't.
- [ ] Generate the first real Alembic migration: `alembic revision --autogenerate -m "initial schema"` then `alembic upgrade head`.
- [ ] Create the first owner account: `python -m app.scripts.create_admin --email you@example.com --role owner`.
- [ ] Set real values in `backend/.env` (`SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`) — never commit `.env`.
- [ ] Add settings rows for delivery fee / tax (`delivery.fee_flat`, `tax.rate_percent`) — Module 9 gives an admin API for this.
- [ ] Obtain TLS certificates (Let's Encrypt recommended) and place in `nginx/certs/`.
- [ ] Update `ALLOWED_HOSTS` and `CORS_ORIGINS` in production `.env` with actual domain names.
- [ ] Configure DNS records for freshcobakers.com / api.freshcobakers.com.

---

## How to update this file after each push
Change the 📦 rows you just pushed to ✅, move finished rows from "Remaining" to "Done", and add the new module's details file.
(I do this for you in every delivery.)
