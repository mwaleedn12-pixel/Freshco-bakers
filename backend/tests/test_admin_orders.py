"""Module 7 — staff order workflow, stock consumption, payments and notifications."""
from tests.helpers import API, make_branch, make_product, stock


def _place(client, cust, pid, qty=2, **body):
    client.post(f"{API}/cart/items", json={"product_id": pid, "quantity": qty}, headers=cust)
    r = client.post(f"{API}/orders", json=body, headers=cust)
    assert r.status_code == 201, r.text
    return r.json()


def _status(client, staff, oid, status, note=None):
    return client.patch(f"{API}/orders/{oid}/status", json={"status": status, "note": note}, headers=staff)


def test_pickup_flow_consumes_stock_and_marks_cash_paid(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    manager = auth_headers("manager", "m@fb.com")
    cust = auth_headers("customer", "c@fb.com")
    pid = make_product(client, admin, price=500)
    bid = make_branch(client, admin)
    stock(client, admin, pid, bid, 10)
    order = _place(client, cust, pid, 3, order_type="PICKUP")
    oid = order["id"]

    # permissions and validation
    assert _status(client, cust, oid, "CONFIRMED").status_code == 403
    assert _status(client, manager, oid, "READY").status_code == 400         # cannot skip steps
    assert _status(client, manager, oid, "OUT_FOR_DELIVERY").status_code == 400

    for st in ("CONFIRMED", "PREPARING", "READY"):
        assert _status(client, manager, oid, st).status_code == 200
    assert _status(client, manager, oid, "DELIVERED").status_code == 400     # pickup order
    done = _status(client, manager, oid, "PICKED_UP", "Collected at counter")
    assert done.status_code == 200
    body = done.json()
    assert body["status"] == "PICKED_UP"
    assert body["payment_status"] == "PAID"                                   # cash collected
    assert body["customer_name"] == "c"
    assert [h["status"] for h in body["status_history"]] == ["PENDING", "CONFIRMED", "PREPARING", "READY", "PICKED_UP"]

    inv = client.get(f"{API}/inventory", headers=manager).json()["items"][0]
    assert inv["quantity"] == 7 and inv["reserved_quantity"] == 0
    sale = client.get(f"{API}/inventory/transactions", params={"type": "SALE"}, headers=manager).json()["items"][0]
    assert sale["quantity"] == -3 and sale["reference_type"] == "order" and sale["reference_id"] == oid

    # finished orders cannot change again
    assert _status(client, manager, oid, "CANCELLED").status_code == 400

    # customer got a notification for every step
    notes = client.get(f"{API}/notifications", headers=cust).json()
    assert notes["unread_count"] >= 5
    assert any("picked up" in (n["message"] or "") for n in notes["items"])


def test_delivery_flow_and_admin_cancel_releases_stock(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "c@fb.com")
    pid = make_product(client, admin)
    bid = make_branch(client, admin)
    stock(client, admin, pid, bid, 10)
    addr = client.post(f"{API}/addresses", json={"line1": "House 1, Street 2", "city": "Lahore"}, headers=cust).json()

    o1 = _place(client, cust, pid, 2, order_type="DELIVERY", address_id=addr["id"])
    for st in ("CONFIRMED", "PREPARING", "READY", "OUT_FOR_DELIVERY", "DELIVERED"):
        assert _status(client, admin, o1["id"], st).status_code == 200
    detail = client.get(f"{API}/orders/admin/{o1['id']}", headers=admin).json()
    assert detail["address"]["line1"] == "House 1, Street 2"
    assert detail["payment_status"] == "PAID"

    # second order gets cancelled by staff -> reservation released
    o2 = _place(client, cust, pid, 4, order_type="PICKUP")
    inv = lambda: client.get(f"{API}/inventory", headers=admin).json()["items"][0]
    assert inv()["reserved_quantity"] == 4
    assert _status(client, admin, o2["id"], "CANCELLED", "Out of cream").status_code == 200
    assert inv()["reserved_quantity"] == 0 and inv()["quantity"] == 8


def test_admin_list_filters_and_payment_updates(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "ayesha@fb.com")
    other = auth_headers("customer", "bilal@fb.com")
    pid = make_product(client, admin)
    o1 = _place(client, cust, pid)
    _place(client, other, pid)
    _status(client, admin, o1["id"], "CONFIRMED")

    listing = lambda **p: client.get(f"{API}/orders/admin/list", params=p, headers=admin).json()
    assert client.get(f"{API}/orders/admin/list", headers=cust).status_code == 403
    assert listing()["total"] == 2
    assert listing(status="CONFIRMED")["total"] == 1
    assert listing(search="bilal")["total"] == 1
    assert listing(search=o1["order_number"])["items"][0]["customer_email"] == "ayesha@fb.com"
    assert listing(order_source="POS")["total"] == 0
    assert listing(date_from="2000-01-01", date_to="2999-01-01")["total"] == 2
    assert listing(date_from="2999-01-01")["total"] == 0

    # payments: UNPAID -> PAID -> REFUNDED, nothing else
    pay = lambda st, ref=None: client.patch(f"{API}/orders/{o1['id']}/payment", json={
        "status": st, "transaction_reference": ref}, headers=admin)
    assert pay("REFUNDED").status_code == 400
    paid = pay("PAID", "TXN-123")
    assert paid.status_code == 200 and paid.json()["payments"][0]["transaction_reference"] == "TXN-123"
    assert pay("PAID").status_code == 400
    assert pay("REFUNDED").json()["payment_status"] == "REFUNDED"


def test_notifications_read_flow(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "c@fb.com")
    pid = make_product(client, admin)
    _place(client, cust, pid)

    # staff were told about the new order, the customer about the received order
    staff_notes = client.get(f"{API}/notifications", headers=admin).json()
    assert any(n["title"] == "New order" for n in staff_notes["items"])
    mine = client.get(f"{API}/notifications", headers=cust).json()
    assert mine["unread_count"] == 1
    nid = mine["items"][0]["id"]

    assert client.get(f"{API}/notifications").status_code == 401
    assert client.patch(f"{API}/notifications/{nid}/read", headers=admin).status_code == 404  # not theirs
    assert client.patch(f"{API}/notifications/{nid}/read", headers=cust).json()["is_read"] is True
    assert client.get(f"{API}/notifications/unread-count", headers=cust).json() == {"unread_count": 0}
    assert client.post(f"{API}/notifications/read-all", headers=admin).json() == {"unread_count": 0}
