# Module 06 — Branches & Inventory

**Status:** ✅ Built & tested (23/23 tests) — waiting for your push
**Delivered together with:** Modules 04, 05, 07, 08

## What this module does
- **Branches** (`/branches`): public list of active branches (for pickup + contact page), admin/owner create/update.
  Branch code is unique and stored upper-case. Branches are never deleted — set `status: inactive` to close one.
- **Inventory** (`/inventory`, manager / admin / owner):
  - list stock per product per branch (quantity, reserved, **available**, minimum, `is_low`), search, `low_stock=true` filter
  - `POST /inventory/adjust` — types `PURCHASE`, `RETURN` (add), `WASTE` (remove), `ADJUSTMENT` (signed correction)
  - `POST /inventory/transfer` — branch to branch (`TRANSFER_OUT` + `TRANSFER_IN`)
  - `PATCH /inventory/{product_id}/{branch_id}/minimum` — low-stock threshold
  - `GET /inventory/transactions` — full history (who, what, when), filter by product / branch / type
- **Rules:** stock can never drop below the units reserved for open orders; every change writes an inventory
  transaction + audit log; a **low stock notification** goes to managers/admins/owners when stock falls to the minimum.
- Shared `inventory_service` is the single place that changes stock (also used by orders in Module 07).

## Files
```
backend/app/schemas/branch.py                 (new)
backend/app/schemas/inventory.py              (new)
backend/app/services/branch_service.py        (new)
backend/app/services/inventory_service.py     (new)
backend/app/services/notification_service.py  (new)
backend/app/api/v1/endpoints/branches.py      (new)
backend/app/api/v1/endpoints/inventory.py     (new)
backend/tests/helpers.py                      (new)
backend/tests/test_inventory.py               (new)
```

## Bug fixed on the way
Audit log snapshots crashed on `time` columns (branch opening hours). Fixed in `services/audit_service.py`.
