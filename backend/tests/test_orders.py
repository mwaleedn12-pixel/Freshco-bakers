"""Module 5 — cart, addresses, checkout, stock reservation, coupons, cancellation."""
from datetime import datetime, timedelta, timezone

from app.models.branch import Branch
from app.models.coupon import Coupon, CouponType
from app.models.inventory import Inventory
from app.models.setting import Setting

API = "/api/v1"


def _make_product(client, admin, sku="CAKE-1", price=500, **extra):
    r = client.post(f"{API}/products", json={"sku": sku, "name": f"Product {sku}", "price": price, **extra},
                    headers=admin)
    assert r.status_code == 201
    return r.json()["id"]


def test_cart_flow(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "cust@fb.com")
    pid = _make_product(client, admin, price=500, sale_price=400)

    assert client.get(f"{API}/cart").status_code == 401
    assert client.get(f"{API}/cart", headers=cust).json()["items"] == []

    cart = client.post(f"{API}/cart/items", json={"product_id": pid, "quantity": 2}, headers=cust).json()
    assert cart["items"][0]["unit_price"] == 400  # sale price is used
    assert cart["subtotal"] == 800

    # adding the same product again accumulates the quantity
    cart = client.post(f"{API}/cart/items", json={"product_id": pid, "quantity": 1}, headers=cust).json()
    assert cart["item_count"] == 3 and len(cart["items"]) == 1

    item_id = cart["items"][0]["id"]
    cart = client.patch(f"{API}/cart/items/{item_id}", json={"quantity": 5}, headers=cust).json()
    assert cart["subtotal"] == 2000
    assert client.post(f"{API}/cart/items", json={"product_id": 999}, headers=cust).status_code == 404
    assert client.delete(f"{API}/cart/items/{item_id}", headers=cust).json()["items"] == []


def test_checkout_totals_coupon_delivery(client, auth_headers, session_factory):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "cust@fb.com")
    pid = _make_product(client, admin, price=500)
    with session_factory() as db:
        db.add_all([
            Setting(key="delivery.fee_flat", value={"amount": 150}),
            Setting(key="tax.rate_percent", value={"percent": 5}),
            Coupon(code="WELCOME10", type=CouponType.PERCENTAGE, value=10, status="active"),
        ])
        db.commit()

    # empty cart
    assert client.post(f"{API}/orders", json={}, headers=cust).status_code == 400

    client.post(f"{API}/cart/items", json={"product_id": pid, "quantity": 2}, headers=cust)

    # delivery needs an address
    assert client.post(f"{API}/orders", json={"order_type": "DELIVERY"}, headers=cust).status_code == 400
    addr = client.post(f"{API}/addresses", json={"line1": "House 12, Street 4", "city": "Lahore"}, headers=cust)
    assert addr.status_code == 201 and addr.json()["is_default"] is True

    # bad coupon and past schedule are rejected and the cart is kept
    body = {"order_type": "DELIVERY", "address_id": addr.json()["id"]}
    assert client.post(f"{API}/orders", json={**body, "coupon_code": "NOPE"}, headers=cust).status_code == 400
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    assert client.post(f"{API}/orders", json={**body, "scheduled_at": past}, headers=cust).status_code == 400

    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    r = client.post(f"{API}/orders", json={**body, "coupon_code": "welcome10", "scheduled_at": future,
                                           "notes": "No nuts please"}, headers=cust)
    assert r.status_code == 201, r.text
    order = r.json()
    # subtotal 1000 - 10% = 900 ; tax 5% of 900 = 45 ; delivery 150 -> 1095
    assert order["subtotal"] == 1000
    assert order["discount_total"] == 100
    assert order["tax_total"] == 45
    assert order["delivery_fee"] == 150
    assert order["total"] == 1095
    assert order["status"] == "PENDING" and order["payment_status"] == "UNPAID"
    assert order["order_source"] == "WEBSITE"
    assert order["order_number"].startswith("FB-")
    assert order["items"][0]["product_name"] == f"Product CAKE-1"
    assert order["payments"][0]["amount"] == 1095
    assert order["status_history"][0]["status"] == "PENDING"

    # cart was emptied
    assert client.get(f"{API}/cart", headers=cust).json()["items"] == []

    # my orders + detail
    listing = client.get(f"{API}/orders", headers=cust).json()
    assert listing["total"] == 1
    assert client.get(f"{API}/orders/{order['id']}", headers=cust).status_code == 200

    # another customer cannot see it, staff can
    other = auth_headers("customer", "other@fb.com")
    assert client.get(f"{API}/orders/{order['id']}", headers=other).status_code == 404
    assert client.get(f"{API}/orders/{order['id']}", headers=admin).status_code == 200


def test_stock_reservation_and_cancel(client, auth_headers, session_factory):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "cust@fb.com")
    pid = _make_product(client, admin, price=300)
    with session_factory() as db:
        branch = Branch(name="Main Branch", code="MAIN")
        db.add(branch)
        db.flush()
        db.add(Inventory(product_id=pid, branch_id=branch.id, quantity=5))
        db.commit()

    def reserved():
        with session_factory() as db:
            return db.query(Inventory).one().reserved_quantity

    client.post(f"{API}/cart/items", json={"product_id": pid, "quantity": 2}, headers=cust)
    first = client.post(f"{API}/orders", json={}, headers=cust)
    assert first.status_code == 201
    assert first.json()["branch_id"] is not None
    assert reserved() == 2

    # only 3 left -> asking for 4 fails and reserves nothing
    client.post(f"{API}/cart/items", json={"product_id": pid, "quantity": 4}, headers=cust)
    too_many = client.post(f"{API}/orders", json={}, headers=cust)
    assert too_many.status_code == 400 and "only 3 left" in too_many.json()["detail"]
    assert reserved() == 2

    # cancelling the first order releases its stock; a second cancel is refused
    cancelled = client.patch(f"{API}/orders/{first.json()['id']}/cancel", headers=cust)
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "CANCELLED"
    assert reserved() == 0
    assert client.patch(f"{API}/orders/{first.json()['id']}/cancel", headers=cust).status_code == 400

    # now 4 is fine
    assert client.post(f"{API}/orders", json={}, headers=cust).status_code == 201
    assert reserved() == 4


def test_unavailable_product_blocks_checkout(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "cust@fb.com")
    pid = _make_product(client, admin)
    client.post(f"{API}/cart/items", json={"product_id": pid}, headers=cust)
    client.put(f"{API}/products/{pid}", json={"is_available": False}, headers=admin)
    r = client.post(f"{API}/orders", json={}, headers=cust)
    assert r.status_code == 400 and "no longer available" in r.json()["detail"]
