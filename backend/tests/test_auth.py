"""
Auth flow integration test — runs against an in-memory SQLite DB shared
across requests via StaticPool, with the app's real DB dependency overridden.
"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_register_login_me_flow():
    register_resp = client.post(
        "/api/v1/auth/register",
        json={"name": "Ali Raza", "email": "ali@example.com", "password": "supersecret123"},
    )
    assert register_resp.status_code == 201
    data = register_resp.json()
    assert data["user"]["email"] == "ali@example.com"
    assert data["user"]["role"] == "customer"
    assert data["access_token"]

    # Duplicate registration must be rejected
    dup_resp = client.post(
        "/api/v1/auth/register",
        json={"name": "Ali Raza", "email": "ali@example.com", "password": "supersecret123"},
    )
    assert dup_resp.status_code == 400

    # Correct login
    login_resp = client.post("/api/v1/auth/login", json={"email": "ali@example.com", "password": "supersecret123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Wrong password
    wrong_resp = client.post("/api/v1/auth/login", json={"email": "ali@example.com", "password": "wrongpass"})
    assert wrong_resp.status_code == 401

    # /me with a valid token
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "ali@example.com"

    # /me without a token must be rejected
    no_auth_resp = client.get("/api/v1/auth/me")
    assert no_auth_resp.status_code == 401
