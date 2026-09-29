"""Small helpers shared by several test files."""
API = "/api/v1"


def make_product(client, admin, sku="CAKE-1", price=500, **extra):
    r = client.post(f"{API}/products", json={"sku": sku, "name": f"Product {sku}", "price": price, **extra},
                    headers=admin)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def make_branch(client, admin, code="MAIN", name="Main Branch"):
    r = client.post(f"{API}/branches", json={"name": name, "code": code, "city": "Lahore",
                                             "opening_time": "08:00:00", "closing_time": "22:00:00"}, headers=admin)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def stock(client, headers, product_id, branch_id, qty):
    r = client.post(f"{API}/inventory/adjust", json={"product_id": product_id, "branch_id": branch_id,
                                                     "type": "PURCHASE", "quantity": qty}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()
