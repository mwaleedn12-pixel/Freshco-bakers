"""
Tests for Module 9: Staff, Customers, Settings & User Profile APIs.
"""
def test_settings_public_and_admin_update(client, auth_headers):
    owner_headers = auth_headers("owner", "owner@freshco.com")
    # Public GET settings
    r = client.get("/api/v1/settings")
    assert r.status_code == 200
    data = r.json()
    assert "bakery.name" in data
    assert data["bakery.name"]["value"] == "Freshco Bakers"

    # Admin bulk update
    payload = {
        "settings": [
            {"key": "bakery.name", "value": "Freshco Premium Bakers", "category": "bakery"},
            {"key": "delivery.fee_flat", "value": 200.0, "category": "delivery"},
        ]
    }
    r2 = client.put("/api/v1/settings", json=payload, headers=owner_headers)
    assert r2.status_code == 200
    updated_data = r2.json()
    assert updated_data["bakery.name"]["value"] == "Freshco Premium Bakers"
    assert updated_data["delivery.fee_flat"]["value"] == 200.0


def test_staff_crud_flow(client, auth_headers):
    owner_headers = auth_headers("owner", "owner@freshco.com")
    # Create cashier staff member
    staff_payload = {
        "name": "Ali Cashier",
        "email": "ali.cashier@freshco.com",
        "phone": "+923001234567",
        "password": "Password123!",
        "role": "cashier",
    }
    r = client.post("/api/v1/staff", json=staff_payload, headers=owner_headers)
    assert r.status_code == 201
    created = r.json()
    assert created["email"] == "ali.cashier@freshco.com"
    assert created["role"] == "cashier"
    staff_id = created["id"]

    # List staff
    r_list = client.get("/api/v1/staff", headers=owner_headers)
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 1

    # Update staff role to manager
    r_up = client.put(f"/api/v1/staff/{staff_id}", json={"role": "manager", "status": "active"}, headers=owner_headers)
    assert r_up.status_code == 200
    assert r_up.json()["role"] == "manager"


def test_customer_list_and_profile_flow(client, auth_headers):
    owner_headers = auth_headers("owner", "owner@freshco.com")
    cust_headers = auth_headers("customer", "customer@freshco.com")

    # Customer updates profile
    r_prof = client.put("/api/v1/auth/profile", json={"name": "Updated Customer Name", "phone": "+923111111111"}, headers=cust_headers)
    assert r_prof.status_code == 200
    assert r_prof.json()["name"] == "Updated Customer Name"

    # Admin/Manager views customers
    r_cust = client.get("/api/v1/customers", headers=owner_headers)
    assert r_cust.status_code == 200
    customers = r_cust.json()
    assert len(customers) >= 1

