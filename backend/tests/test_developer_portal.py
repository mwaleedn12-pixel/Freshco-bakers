import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_dashboard_endpoint(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Freshco Bakers" in r.text
    assert "Backend Control Hub" in r.text


def test_custom_swagger_docs(client):
    r = client.get("/api/v1/docs")
    assert r.status_code == 200
    assert "Swagger UI" in r.text
    assert "swagger-ui" in r.text

    r_alias = client.get("/docs")
    assert r_alias.status_code == 200
    assert "Swagger UI" in r_alias.text


def test_scalar_docs(client):
    r = client.get("/scalar")
    assert r.status_code == 200
    assert "@scalar/api-reference" in r.text


def test_system_info(client):
    r = client.get("/api/v1/system/info")
    assert r.status_code == 200
    data = r.json()
    assert data["app_name"] == "Freshco Bakers"
    assert data["version"] == "1.0.0"
    assert "uptime_seconds" in data
    assert "python_version" in data


def test_system_stats(client):
    r = client.get("/api/v1/system/stats")
    assert r.status_code == 200
    data = r.json()
    assert "database" in data
    assert "products" in data


def test_root_content_negotiation(client):
    # API client default
    r_json = client.get("/", headers={"Accept": "application/json"})
    assert r_json.status_code == 200
    assert "Freshco Bakers API is running" in r_json.json()["message"]

    # Browser simulation
    r_html = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert r_html.status_code == 200
    assert "Backend Control Hub" in r_html.text
