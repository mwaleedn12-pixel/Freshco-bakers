"""Module 6 — branches and inventory."""
from tests.helpers import API, make_branch, make_product, stock


def test_branches_crud_and_permissions(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    cust = auth_headers("customer", "c@fb.com")
    body = {"name": "Gulberg", "code": "glb", "city": "Lahore", "opening_time": "09:00:00", "closing_time": "21:30:00"}

    assert client.post(f"{API}/branches", json=body, headers=cust).status_code == 403
    created = client.post(f"{API}/branches", json=body, headers=admin)
    assert created.status_code == 201
    assert created.json()["code"] == "GLB"  # upper-cased
    assert created.json()["closing_time"] == "21:30:00"
    assert client.post(f"{API}/branches", json=body, headers=admin).status_code == 409  # duplicate code

    bid = created.json()["id"]
    assert client.get(f"{API}/branches").json()[0]["name"] == "Gulberg"  # public
    client.put(f"{API}/branches/{bid}", json={"status": "inactive"}, headers=admin)
    assert client.get(f"{API}/branches").json() == []
    assert client.get(f"{API}/branches/{bid}").status_code == 404
    assert len(client.get(f"{API}/branches/admin/list", headers=admin).json()) == 1


def test_stock_adjustments_transactions_and_low_stock(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    manager = auth_headers("manager", "m@fb.com")
    cust = auth_headers("customer", "c@fb.com")
    pid = make_product(client, admin)
    bid = make_branch(client, admin)

    assert client.get(f"{API}/inventory", headers=cust).status_code == 403

    row = stock(client, manager, pid, bid, 20)
    assert row["quantity"] == 20 and row["available_quantity"] == 20

    def adjust(type_, qty):
        return client.post(f"{API}/inventory/adjust", json={"product_id": pid, "branch_id": bid, "type": type_,
                                                            "quantity": qty}, headers=manager)

    assert adjust("WASTE", 3).json()["quantity"] == 17
    assert adjust("ADJUSTMENT", -2).json()["quantity"] == 15
    assert adjust("RETURN", 1).json()["quantity"] == 16
    assert adjust("WASTE", 0).status_code == 400
    assert adjust("WASTE", -5).status_code == 400
    assert adjust("ADJUSTMENT", 0).status_code == 400
    assert adjust("WASTE", 100).status_code == 400  # would go below zero / reserved

    # minimum + low stock alert (manager gets a notification when stock drops under the minimum)
    client.patch(f"{API}/inventory/{pid}/{bid}/minimum", json={"minimum_quantity": 15}, headers=manager)
    assert client.get(f"{API}/inventory", params={"low_stock": True}, headers=manager).json()["total"] == 0
    adjust("WASTE", 2)  # 14 <= 15
    low = client.get(f"{API}/inventory", params={"low_stock": True}, headers=manager).json()
    assert low["total"] == 1 and low["items"][0]["is_low"] is True
    notes = client.get(f"{API}/notifications", headers=manager).json()
    assert any(n["type"] == "low_stock" for n in notes["items"])

    tx = client.get(f"{API}/inventory/transactions", params={"product_id": pid}, headers=manager).json()
    assert tx["total"] == 5  # purchase + waste + adjustment + return + waste
    assert [t["quantity"] for t in tx["items"]][:2] == [-2, 1]
    assert all(t["created_by"] is not None for t in tx["items"])
    only_waste = client.get(f"{API}/inventory/transactions", params={"type": "WASTE"}, headers=manager).json()
    assert only_waste["total"] == 2


def test_transfer_between_branches(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    pid = make_product(client, admin)
    a = make_branch(client, admin, "BR-A", "Branch A")
    b = make_branch(client, admin, "BR-B", "Branch B")
    stock(client, admin, pid, a, 10)

    def transfer(frm, to, qty):
        return client.post(f"{API}/inventory/transfer", json={"product_id": pid, "from_branch_id": frm,
                                                              "to_branch_id": to, "quantity": qty}, headers=admin)

    assert transfer(a, a, 1).status_code == 400
    assert transfer(a, b, 11).status_code == 400  # not enough
    ok = transfer(a, b, 4)
    assert ok.status_code == 200
    assert [r["quantity"] for r in ok.json()] == [6, 4]
    types = {t["type"] for t in client.get(f"{API}/inventory/transactions", headers=admin).json()["items"]}
    assert {"TRANSFER_OUT", "TRANSFER_IN"} <= types
