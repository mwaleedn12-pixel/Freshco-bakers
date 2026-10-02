# Module 08 — Coupons Admin, Custom Cakes & Reviews

**Status:** ✅ Built & tested (23/23 tests) — waiting for your push
**Delivered together with:** Modules 04, 05, 06, 07

## What this module does
- **Coupons** (`/coupons`, admin / owner): create, list (filter by status), update, delete (only if never used — otherwise deactivate).
  Percentage (max 100) or fixed, minimum order, total + per-customer limits, start / expiry dates, codes stored upper-case.
  Customers can preview a coupon with `POST /coupons/validate` (same rules as checkout).
- **Custom cakes** (`/custom-cakes`): customer submits flavour, size, cream, theme, message, reference image URL and needed-by date →
  staff quote a price → customer accepts → `in_progress` → `done` (or `rejected` / `cancelled`). Only valid steps are allowed,
  internal staff notes are never shown to customers, and both sides get notifications.
- **Reviews** (`/reviews`): only customers who actually received the product (order delivered / picked up) can review it, once per product.
  Reviews start as `pending`; staff approve / reject. Public `GET /reviews/product/{id}` returns approved reviews,
  average rating and 1-5 star distribution (customer shown by first name only).

## Files
```
backend/app/schemas/coupon.py                 (new)
backend/app/schemas/custom_cake.py            (new)
backend/app/schemas/review.py                 (new)
backend/app/services/coupon_service.py        (new)
backend/app/services/custom_cake_service.py   (new)
backend/app/services/review_service.py        (new)
backend/app/api/v1/endpoints/coupons.py       (new)
backend/app/api/v1/endpoints/custom_cakes.py  (new)
backend/app/api/v1/endpoints/reviews.py       (new)
backend/app/api/v1/__init__.py                (replaced — registers every router up to Module 08)
backend/tests/test_coupons.py                 (new)
backend/tests/test_custom_cakes.py            (new)
backend/tests/test_reviews.py                 (new)
```
