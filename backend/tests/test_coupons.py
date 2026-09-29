"""Module 8a — coupons admin + validation preview + usage limits."""
from datetime import datetime, timedelta, timezone

from tests.helpers import API, make_product


def _coupon(client, admin, **extra):
    body = {"code": "eid20", "type": "PERCENTAGE", "value": 20, **extra}
    return client.post(f"{API}/coupons", json=body, headers=admin)


def test_coupon_crud_and_rules(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "c@fb.com")

    assert _coupon(client, cust).status_code == 403
    created = _coupon(client, admin, min_order_amount=500, usage_limit=10)
    assert created.status_code == 201
    assert created.json()["code"] == "EID20" and created.json()["times_used"] == 0
    assert _coupon(client, admin).status_code == 409                        # duplicate
    assert _coupon(client, admin, code="BAD", value=150).status_code == 422  # >100%
    past, future = (datetime.now(timezone.utc) + timedelta(days=d) for d in (-2, 5))
    assert _coupon(client, admin, code="DATES", starts_at=future.isoformat(),
                   expires_at=past.isoformat()).status_code == 422

    cid = created.json()["id"]
    upd = client.put(f"{API}/coupons/{cid}", json={"value": 25, "status": "inactive"}, headers=admin)
    assert upd.json()["value"] == 25 and upd.json()["status"] == "inactive"
    assert client.put(f"{API}/coupons/{cid}", json={"value": 150}, headers=admin).status_code == 400
    assert len(client.get(f"{API}/coupons", params={"status": "inactive"}, headers=admin).json()) == 1
    assert client.delete(f"{API}/coupons/{cid}", headers=admin).status_code == 204
    assert client.get(f"{API}/coupons/{cid}", headers=admin).status_code == 404


def test_validate_and_usage_limits_at_checkout(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "c@fb.com")
    pid = make_product(client, admin, price=1000)
    _coupon(client, admin, code="ONCE", type="FIXED", value=150, min_order_amount=500, per_customer_limit=1)

    check = lambda code, sub: client.post(f"{API}/coupons/validate", json={"code": code, "subtotal": sub}, headers=cust)
    assert client.post(f"{API}/coupons/validate", json={"code": "ONCE", "subtotal": 900}).status_code == 401
    ok = check("once", 900)
    assert ok.status_code == 200
    assert ok.json() == {"code": "ONCE", "discount_amount": 150, "subtotal_after_discount": 750}
    assert check("ONCE", 100).status_code == 400 and "Minimum" in check("ONCE", 100).json()["detail"]
    assert check("NOPE", 900).status_code == 400

    # use it once at checkout -> second use blocked, used coupon cannot be deleted
    client.post(f"{API}/cart/items", json={"product_id": pid}, headers=cust)
    order = client.post(f"{API}/orders", json={"coupon_code": "ONCE"}, headers=cust).json()
    assert order["discount_total"] == 150 and order["total"] == 850
    assert check("ONCE", 900).status_code == 400
    coupon = client.get(f"{API}/coupons", headers=admin).json()[0]
    assert coupon["times_used"] == 1
    assert client.delete(f"{API}/coupons/{coupon['id']}", headers=admin).status_code == 400

    # cancelling the order gives the coupon use back
    client.patch(f"{API}/orders/{order['id']}/cancel", headers=cust)
    assert check("ONCE", 900).status_code == 200
