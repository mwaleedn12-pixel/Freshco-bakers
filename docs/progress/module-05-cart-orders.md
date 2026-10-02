# Module 05 — Cart, Addresses, Checkout & Orders (customer side)

**Status:** ✅ Ready to push
**Date:** 2026-09-28
**Delivered together with:** Module 04

## What this module does
- **Cart** (`/cart`): get, add item (same product accumulates), change quantity, remove item, clear.
  Shows current server-side prices (sale price if set).
- **Addresses** (`/addresses`): list, add (first one becomes default), delete.
- **Checkout** (`POST /orders`): converts the cart into an order.
  - Prices always come from the database, never from the app.
  - Pickup or delivery (delivery needs one of the customer's own addresses), optional future `scheduled_at`, notes.
  - Optional coupon: percentage/fixed, active, start/expiry dates, minimum order, total and per-customer limits.
  - Delivery fee from setting `delivery.fee_flat` `{"amount": N}` and tax from `tax.rate_percent` `{"percent": N}`
    (both default to 0 until the Settings module exists).
  - Order = `PENDING`, payment = `UNPAID` (kept separate), `order_source = WEBSITE`, number `FB-000001`.
  - `order_items` store product name + price snapshots; payment row (CASH or ONLINE) and status history are created.
  - **Stock is reserved** (`reserved_quantity`) to prevent overselling; rows are locked on PostgreSQL.
    If a product has no inventory row for the branch, stock is treated as not limited (the Inventory module will configure it).
  - Cart is emptied on success; nothing changes if any check fails.
- **Orders** (`/orders`): my orders (paginated), order detail with status history (owner of the order, or staff),
  `PATCH /orders/{id}/cancel` (only PENDING/CONFIRMED) which releases reserved stock and frees the coupon use.

## Not in this module (planned next)
Admin order workflow (confirm/prepare/ready/deliver, deducting stock), payments gateway, coupons admin CRUD,
branches & inventory admin, custom cakes, reviews.

## Files added / changed
```
backend/app/api/v1/endpoints/cart.py         (new)
backend/app/api/v1/endpoints/addresses.py    (new)
backend/app/api/v1/endpoints/orders.py       (new)
backend/app/schemas/cart.py                  (new)
backend/app/schemas/address.py               (new)
backend/app/schemas/order.py                 (new)
backend/app/services/pricing.py              (new)
backend/app/services/cart_service.py         (new)
backend/app/services/address_service.py      (new)
backend/app/services/order_service.py        (new)
backend/tests/test_orders.py                 (new)
```
(`api/v1/__init__.py` from Module 4 already registers these routers.)

## Tests
Full suite: **10/10 passing** — cart flow, checkout totals with coupon + delivery + tax, permissions on orders,
stock reservation / insufficient stock / cancel releases stock, unavailable product blocks checkout.

## Git commit used
```
Module 5: cart, addresses, checkout and customer orders (coupons, stock reservation, cancel)
```
