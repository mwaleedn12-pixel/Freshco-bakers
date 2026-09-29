"""Module 8b — custom cake requests: request -> quote -> accept -> in progress -> done."""
from datetime import date, timedelta

from tests.helpers import API


def _request(client, cust, **extra):
    body = {"type": "birthday", "flavour": "Chocolate", "size": "2 lb", "cream": "Whipped", "theme": "Unicorn",
            "message": "Happy Birthday Sara", "requested_date": (date.today() + timedelta(days=7)).isoformat(), **extra}
    return client.post(f"{API}/custom-cakes", json=body, headers=cust)


def test_full_custom_cake_flow(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "sara@fb.com")
    other = auth_headers("customer", "other@fb.com")

    assert client.post(f"{API}/custom-cakes", json={}).status_code == 401
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    assert _request(client, cust, requested_date=yesterday).status_code == 400

    created = _request(client, cust)
    assert created.status_code == 201
    req = created.json()
    assert req["status"] == "pending" and "notes" not in req
    rid = req["id"]

    # staff were notified; other customers cannot see the request
    assert any(n["title"] == "New custom cake request"
               for n in client.get(f"{API}/notifications", headers=admin).json()["items"])
    assert client.get(f"{API}/custom-cakes/{rid}", headers=other).status_code == 404
    assert client.get(f"{API}/custom-cakes/{rid}", headers=admin).status_code == 200

    # customer cannot quote / accept before a quote exists
    assert client.patch(f"{API}/custom-cakes/{rid}/quote", json={"quote_amount": 3500}, headers=cust).status_code == 403
    assert client.patch(f"{API}/custom-cakes/{rid}/accept", headers=cust).status_code == 400

    quoted = client.patch(f"{API}/custom-cakes/{rid}/quote", json={"quote_amount": 3500, "notes": "Fondant extra"},
                          headers=admin)
    assert quoted.status_code == 200
    assert quoted.json()["status"] == "quoted" and quoted.json()["notes"] == "Fondant extra"
    assert quoted.json()["customer_name"] == "sara"
    # customer sees the price but never the internal notes
    mine = client.get(f"{API}/custom-cakes/{rid}", headers=cust).json()
    assert mine["quote_amount"] == 3500 and "notes" not in mine
    assert client.patch(f"{API}/custom-cakes/{rid}/status", json={"status": "done"}, headers=admin).status_code == 400

    assert client.patch(f"{API}/custom-cakes/{rid}/accept", headers=other).status_code == 404
    assert client.patch(f"{API}/custom-cakes/{rid}/accept", headers=cust).json()["status"] == "accepted"
    for st in ("in_progress", "done"):
        r = client.patch(f"{API}/custom-cakes/{rid}/status", json={"status": st}, headers=admin)
        assert r.status_code == 200 and r.json()["status"] == st
    assert client.patch(f"{API}/custom-cakes/{rid}/cancel", headers=cust).status_code == 400

    texts = " ".join(n["message"] or "" for n in client.get(f"{API}/notifications", headers=cust).json()["items"])
    assert "quotation" in texts.lower() and "ready" in texts


def test_cancel_reject_and_listing(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "sara@fb.com")
    first = _request(client, cust).json()["id"]
    second = _request(client, cust, flavour="Vanilla").json()["id"]

    assert client.patch(f"{API}/custom-cakes/{first}/cancel", headers=cust).json()["status"] == "cancelled"
    assert client.patch(f"{API}/custom-cakes/{second}/status", json={"status": "rejected", "notes": "Fully booked"},
                        headers=admin).json()["status"] == "rejected"

    assert client.get(f"{API}/custom-cakes", headers=cust).json()["total"] == 2
    assert client.get(f"{API}/custom-cakes/admin/list", headers=cust).status_code == 403
    listing = client.get(f"{API}/custom-cakes/admin/list", params={"status": "rejected"}, headers=admin).json()
    assert listing["total"] == 1 and listing["items"][0]["notes"] == "Fully booked"
