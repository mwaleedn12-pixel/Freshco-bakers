# Module 07 — Admin Orders Workflow & Notifications

**Status:** ✅ Built & tested (23/23 tests) — waiting for your push
**Delivered together with:** Modules 04, 05, 06, 08

## What this module does
- **Staff order list** `GET /orders/admin/list` (manager / admin / owner): filter by status, payment status, source
  (WEBSITE/POS/PHONE/WHATSAPP), type, branch, date range and search (order number, customer name/phone/email);
  paginated, with customer details. `GET /orders/admin/{id}` gives the full detail incl. address and status history.
- **Status workflow** `PATCH /orders/{id}/status` — only valid steps are accepted:
  `PENDING → CONFIRMED → PREPARING → READY → OUT_FOR_DELIVERY → DELIVERED` (delivery) or `READY → PICKED_UP` (pickup);
  `CANCELLED` allowed until READY. Every step is stored in the status history and audit log.
- **Stock:** cancelling releases the reservation; DELIVERED / PICKED_UP consumes it and writes a `SALE` inventory transaction.
- **Cash orders** are marked PAID automatically when delivered / picked up.
- **Payment status** `PATCH /orders/{id}/payment`: `UNPAID/FAILED → PAID` (with transaction reference), `PAID → REFUNDED`,
  `UNPAID → FAILED`. (Real gateway integration comes in the Payments module.)
- **Notifications** (`/notifications`): every user gets in-app notifications — customers on order placed / each status change /
  payment changes / cake quotes; staff on new orders, cancellations, new cake requests, reviews to moderate, low stock.
  Endpoints: list (unread filter, pagination + unread count), unread-count, mark one read, mark all read.

## Files
```
backend/app/services/order_admin_service.py   (new)
backend/app/services/order_service.py         (replaced — notifications, shared inventory logic, public apply_coupon)
backend/app/schemas/order.py                  (replaced — staff schemas added)
backend/app/api/v1/endpoints/orders.py        (replaced — staff routes added)
backend/app/schemas/notification.py           (new)
backend/app/api/v1/endpoints/notifications.py (new)
backend/tests/test_admin_orders.py            (new)
```
