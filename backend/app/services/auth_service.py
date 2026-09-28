"""
Auth service — registration, login, and JWT issuance.
Every new customer signup is assigned the default "customer" role
(roles are created on first use so a fresh DB doesn't need manual seeding).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role, User

DEFAULT_ROLE_NAME = "customer"


def get_or_create_role(db: Session, name: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role is None:
        role = Role(name=name, description=f"{name.capitalize()} role")
        db.add(role)
        db.flush()
    return role


def register_user(db: Session, *, name: str, email: str, phone: str | None, password: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise ValueError("A user with this email already exists")

    role = get_or_create_role(db, DEFAULT_ROLE_NAME)
    user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def issue_token(user: User) -> str:
    role_name = user.role.name if user.role else None
    return create_access_token(subject=str(user.id), extra_claims={"role": role_name, "email": user.email})
