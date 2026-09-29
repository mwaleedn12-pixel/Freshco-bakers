"""Module 8c — reviews: purchase check, moderation, public rating summary."""
from tests.helpers import API, make_product


def _deliver_order(client, admin, cust, pid):
    client.post(f"{API}/cart/items", json={"product_id": pid}, headers=cust)
    oid = client.post(f"{API}/orders", json={}, headers=cust).json()["id"]
    for st in ("CONFIRMED", "PREPARING", "READY", "PICKED_UP"):
        assert client.patch(f"{API}/orders/{oid}/status", json={"status": st}, headers=admin).status_code == 200
    return oid


def test_review_rules_and_moderation(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    buyer = auth_headers("customer", "a@fb.com")
    stranger = auth_headers("customer", "s@fb.com")
    pid = make_product(client, admin)
    review = {"product_id": pid, "rating": 5, "comment": "Best cake ever!"}

    assert client.post(f"{API}/reviews", json=review).status_code == 401
    # no purchase yet
    assert client.post(f"{API}/reviews", json=review, headers=buyer).status_code == 403
    # an order that is only placed (not received) is not enough
    client.post(f"{API}/cart/items", json={"product_id": pid}, headers=buyer)
    client.post(f"{API}/orders", json={}, headers=buyer)
    assert client.post(f"{API}/reviews", json=review, headers=buyer).status_code == 403

    # complete an order -> now allowed, but only once
    admin_orders = client.get(f"{API}/orders/admin/list", headers=admin).json()["items"]
    oid = admin_orders[0]["id"]
    for st in ("CONFIRMED", "PREPARING", "READY", "PICKED_UP"):
        client.patch(f"{API}/orders/{oid}/status", json={"status": st}, headers=admin)
    assert client.post(f"{API}/reviews", json={**review, "rating": 6}, headers=buyer).status_code == 422
    created = client.post(f"{API}/reviews", json=review, headers=buyer)
    assert created.status_code == 201 and created.json()["status"] == "pending"
    assert client.post(f"{API}/reviews", json=review, headers=buyer).status_code == 409
    assert client.post(f"{API}/reviews", json=review, headers=stranger).status_code == 403

    # pending reviews are invisible publicly until approved
    public = lambda: client.get(f"{API}/reviews/product/{pid}").json()
    assert public()["review_count"] == 0 and public()["average_rating"] == 0
    assert client.get(f"{API}/reviews/admin/list", headers=buyer).status_code == 403
    pending = client.get(f"{API}/reviews/admin/list", params={"status": "pending"}, headers=admin).json()
    assert pending["total"] == 1

    rid = created.json()["id"]
    assert client.patch(f"{API}/reviews/{rid}/moderate", json={"status": "approved"}, headers=buyer).status_code == 403
    assert client.patch(f"{API}/reviews/{rid}/moderate", json={"status": "approved"}, headers=admin).status_code == 200
    summary = public()
    assert summary["review_count"] == 1 and summary["average_rating"] == 5.0
    assert summary["distribution"] == {"1": 0, "2": 0, "3": 0, "4": 0, "5": 1}
    assert summary["items"][0]["comment"] == "Best cake ever!"

    # rejected again -> hidden; my reviews still lists it
    client.patch(f"{API}/reviews/{rid}/moderate", json={"status": "rejected"}, headers=admin)
    assert public()["review_count"] == 0
    assert client.get(f"{API}/reviews/mine", headers=buyer).json()["total"] == 1


def test_average_over_several_reviews_uses_first_name_only(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    pid = make_product(client, admin)
    for email, rating in (("one@fb.com", 5), ("two@fb.com", 4), ("three@fb.com", 3)):
        cust = auth_headers("customer", email)
        _deliver_order(client, admin, cust, pid)
        rid = client.post(f"{API}/reviews", json={"product_id": pid, "rating": rating}, headers=cust).json()["id"]
        client.patch(f"{API}/reviews/{rid}/moderate", json={"status": "approved"}, headers=admin)
    summary = client.get(f"{API}/reviews/product/{pid}").json()
    assert summary["review_count"] == 3 and summary["average_rating"] == 4.0
    assert {i["customer_name"] for i in summary["items"]} == {"one", "two", "three"}
    assert client.get(f"{API}/reviews/product/999").status_code == 404
