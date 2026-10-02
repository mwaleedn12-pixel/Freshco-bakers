"""
Tests for Modules 10–13: Payments & Thermal Receipts, Analytics, POS Phase 2, Expenses & Audit Logs.
"""
def test_payments_and_thermal_receipt(client, auth_headers):
    cust_headers = auth_headers("customer", "cust_pay@freshco.com")
    owner_headers = auth_headers("owner", "owner_pay@freshco.com")

    # 1. Create product & cart item
    prod_r = client.post("/api/v1/products", json={"sku": "CAKE-PAY-01", "name": "Pay Cake", "price": 1000.0, "category_id": None}, headers=owner_headers)
    assert prod_r.status_code == 201
    prod_id = prod_r.json()["id"]

    client.post("/api/v1/cart/items", json={"product_id": prod_id, "quantity": 1}, headers=cust_headers)

    # 2. Checkout order
    ord_r = client.post("/api/v1/orders", json={"order_type": "PICKUP"}, headers=cust_headers)
    assert ord_r.status_code == 201
    order_id = ord_r.json()["id"]

    # 3. Process payment
    pay_r = client.post("/api/v1/payments/process", json={"order_id": order_id, "method": "CARD", "amount": 1050.0}, headers=cust_headers)
    assert pay_r.status_code == 201
    assert pay_r.json()["status"] == "PAID"

    # 4. Thermal receipt fetch
    rec_r = client.get(f"/api/v1/payments/receipt/{order_id}", headers=cust_headers)
    assert rec_r.status_code == 200
    receipt = rec_r.json()
    assert receipt["bakery_name"] == "Freshco Bakers"
    assert receipt["payment_status"] == "PAID"


def test_pos_sale_and_return_flow(client, auth_headers):
    owner_headers = auth_headers("owner", "pos_owner@freshco.com")
    cashier_headers = auth_headers("cashier", "pos_cashier@freshco.com")

    # Create product
    prod_r = client.post("/api/v1/products", json={"sku": "POS-ITEM-01", "barcode": "890123456", "name": "Croissant", "price": 250.0}, headers=owner_headers)
    assert prod_r.status_code == 201
    prod_id = prod_r.json()["id"]


    # Barcode lookup test
    bc_r = client.get("/api/v1/pos/barcode/890123456", headers=cashier_headers)
    assert bc_r.status_code == 200
    assert bc_r.json()["name"] == "Croissant"

    # Direct POS Sale
    sale_payload = {
        "items": [{"product_id": prod_id, "quantity": 2, "discount": 0.0}],
        "payment_method": "CASH",
        "amount_paid": 525.0,
    }
    sale_r = client.post("/api/v1/pos/sales", json=sale_payload, headers=cashier_headers)
    assert sale_r.status_code == 201
    pos_order = sale_r.json()
    assert pos_order["order_source"] == "POS"
    assert pos_order["payment_status"] == "PAID"
    order_item_id = pos_order["items"][0]["id"]

    # POS Return
    return_payload = {
        "order_id": pos_order["id"],
        "items": [{"order_item_id": order_item_id, "quantity": 1, "reason": "Damaged"}],
    }
    ret_r = client.post("/api/v1/pos/returns", json=return_payload, headers=cashier_headers)
    assert ret_r.status_code == 200
    assert ret_r.json()["refund_amount"] > 0


def test_analytics_expenses_and_audit_logs(client, auth_headers):
    owner_headers = auth_headers("owner", "owner_analytics@freshco.com")

    # Expenses creation
    exp_r = client.post("/api/v1/expenses", json={"category": "Utilities", "amount": 1500.0, "expense_date": "2026-10-02"}, headers=owner_headers)
    assert exp_r.status_code == 201

    # Analytics dashboard
    dash_r = client.get("/api/v1/analytics/dashboard", headers=owner_headers)
    assert dash_r.status_code == 200
    assert "revenue" in dash_r.json()

    # Net profit summary
    profit_r = client.get("/api/v1/expenses/net-profit", headers=owner_headers)
    assert profit_r.status_code == 200
    assert "net_profit" in profit_r.json()

    # Audit logs list
    audit_r = client.get("/api/v1/audit-logs", headers=owner_headers)
    assert audit_r.status_code == 200
    assert len(audit_r.json()) >= 1
