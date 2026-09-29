"""Module 4 — categories & products: permissions, CRUD, public vs admin views, audit logs."""
from app.models.audit_log import AuditLog

API = "/api/v1"


def test_category_permissions_and_crud(client, auth_headers):
    admin = auth_headers("admin", "admin@fb.com")
    customer = auth_headers("customer", "cust@fb.com")
    body = {"name": "Cakes & Pastries"}

    assert client.post(f"{API}/categories", json=body).status_code == 401
    assert client.post(f"{API}/categories", json=body, headers=customer).status_code == 403

    created = client.post(f"{API}/categories", json=body, headers=admin)
    assert created.status_code == 201
    cat = created.json()
    assert cat["slug"] == "cakes-pastries"

    # same name again -> unique slug
    again = client.post(f"{API}/categories", json=body, headers=admin).json()
    assert again["slug"] == "cakes-pastries-2"

    # sub-category + public list
    sub = client.post(f"{API}/categories", json={"name": "Birthday", "parent_id": cat["id"]}, headers=admin)
    assert sub.status_code == 201
    assert len(client.get(f"{API}/categories").json()) == 3

    # inactive categories are hidden from the public but visible to admin
    client.put(f"{API}/categories/{again['id']}", json={"status": "inactive"}, headers=admin)
    assert len(client.get(f"{API}/categories").json()) == 2
    assert len(client.get(f"{API}/categories/admin/list", headers=admin).json()) == 3
    assert client.get(f"{API}/categories/{again['id']}").status_code == 404

    # cannot delete a category that still has a sub-category
    assert client.delete(f"{API}/categories/{cat['id']}", headers=admin).status_code == 400
    assert client.delete(f"{API}/categories/{again['id']}", headers=admin).status_code == 204


def test_product_crud_visibility_and_audit(client, auth_headers, session_factory):
    admin = auth_headers("admin", "admin@fb.com")
    customer = auth_headers("customer", "cust@fb.com")
    cat = client.post(f"{API}/categories", json={"name": "Cakes"}, headers=admin).json()

    payload = {"sku": "CAKE-001", "name": "Chocolate Fudge Cake", "category_id": cat["id"],
               "price": 1800, "cost_price": 900, "description": "Rich and moist", "is_featured": True}
    assert client.post(f"{API}/products", json=payload, headers=customer).status_code == 403

    created = client.post(f"{API}/products", json=payload, headers=admin)
    assert created.status_code == 201
    product = created.json()
    assert product["cost_price"] == 900  # admin sees cost price
    assert product["slug"] == "chocolate-fudge-cake"

    # duplicate SKU, bad sale price, unknown category
    assert client.post(f"{API}/products", json=payload, headers=admin).status_code == 409
    bad_sale = {**payload, "sku": "CAKE-002", "sale_price": 2000}
    assert client.post(f"{API}/products", json=bad_sale, headers=admin).status_code == 400
    bad_cat = {**payload, "sku": "CAKE-003", "category_id": 9999}
    assert client.post(f"{API}/products", json=bad_cat, headers=admin).status_code == 404

    # public view hides cost_price
    public = client.get(f"{API}/products/{product['id']}").json()
    assert "cost_price" not in public
    assert public["price"] == 1800

    # second product, then filters / search / pagination
    client.post(f"{API}/products", json={"sku": "BREAD-1", "name": "Sourdough Loaf", "price": 450}, headers=admin)
    page = client.get(f"{API}/products").json()
    assert page["total"] == 2
    assert client.get(f"{API}/products", params={"category_id": cat["id"]}).json()["total"] == 1
    assert client.get(f"{API}/products", params={"search": "sourdough"}).json()["total"] == 1
    assert client.get(f"{API}/products", params={"featured": True}).json()["total"] == 1
    assert len(client.get(f"{API}/products", params={"limit": 1}).json()["items"]) == 1

    # update (sale price) + images (first image becomes primary)
    upd = client.put(f"{API}/products/{product['id']}", json={"sale_price": 1500}, headers=admin)
    assert upd.status_code == 200 and upd.json()["sale_price"] == 1500
    img = client.post(f"{API}/products/{product['id']}/images", json={"image_url": "https://x.test/a.jpg"}, headers=admin)
    assert img.status_code == 201
    assert img.json()["images"][0]["is_primary"] is True
    image_id = img.json()["images"][0]["id"]
    removed = client.delete(f"{API}/products/{product['id']}/images/{image_id}", headers=admin)
    assert removed.json()["images"] == []

    # archive = hidden publicly, still visible to admin
    assert client.delete(f"{API}/products/{product['id']}", headers=admin).status_code == 204
    assert client.get(f"{API}/products/{product['id']}").status_code == 404
    assert client.get(f"{API}/products").json()["total"] == 1
    admin_list = client.get(f"{API}/products/admin/list", headers=admin).json()
    assert admin_list["total"] == 2
    assert client.get(f"{API}/products/admin/list", headers=customer).status_code == 403

    # every admin change was audited
    with session_factory() as db:
        actions = {a.action for a in db.query(AuditLog).all()}
    assert {"category.create", "product.create", "product.update", "product.archive",
            "product.image_add", "product.image_remove"} <= actions
