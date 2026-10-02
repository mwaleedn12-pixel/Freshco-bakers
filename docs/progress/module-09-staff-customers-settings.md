# Module 09 — Staff Management, Customer Analytics & Settings API

Pushed / Built status: ✅ Complete & Tested

## 1. Features Delivered
- **Staff Accounts Management**: `GET /api/v1/staff`, `POST /api/v1/staff`, `PUT /api/v1/staff/{id}` (Cashier, Manager, Admin, Owner role assignments & activation control).
- **Customer Lifetime Analytics & Profiles**: `GET /api/v1/customers`, `GET /api/v1/customers/{id}` with total spend, order counts, repeat customer status, and addresses.
- **Bakery Store Settings**: Key-value settings for bakery branding, flat delivery fees, tax rates, payment toggles, and notification settings (`GET/PUT /api/v1/settings`).
- **User Self-Service Profile & Security**: `PUT /api/v1/auth/profile` and `POST /api/v1/auth/change-password`.

## 2. Key Files Modified/Added
- `backend/app/schemas/staff.py`
- `backend/app/schemas/customer.py`
- `backend/app/schemas/setting.py`
- `backend/app/services/staff_service.py`
- `backend/app/services/customer_service.py`
- `backend/app/services/setting_service.py`
- `backend/app/api/v1/endpoints/staff.py`
- `backend/app/api/v1/endpoints/customers.py`
- `backend/app/api/v1/endpoints/settings.py`
- `backend/tests/test_module_09.py`
