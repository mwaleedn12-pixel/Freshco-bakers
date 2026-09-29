"""
Shared test fixtures. Every test gets a brand-new in-memory SQLite database
(same connection shared with the app via StaticPool), so tests never affect each other.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.services.auth_service import get_or_create_role, issue_token


@pytest.fixture(autouse=True)
def session_factory():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield factory
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(session_factory):
    """auth_headers("admin", "a@x.com") -> {"Authorization": "Bearer ..."} (creates the user + role if needed)."""

    def make(role_name: str, email: str) -> dict:
        with session_factory() as db:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                role = get_or_create_role(db, role_name)
                user = User(name=email.split("@")[0], email=email, password_hash="not-a-real-hash", role_id=role.id)
                db.add(user)
                db.commit()
                db.refresh(user)
            token = issue_token(user)
        return {"Authorization": f"Bearer {token}"}

    return make
