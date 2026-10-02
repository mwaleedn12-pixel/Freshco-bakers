"""
Staff & Employee Management Service.
Handles role checks, staff account creation, role changes, and listings.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import Role, User
from app.services.audit_service import log_action


def get_role_by_name(db: Session, name: str) -> Role | None:
    return db.scalar(select(Role).where(Role.name == name))


def list_staff(db: Session, role: str | None = None) -> list[User]:
    stmt = select(User).join(User.role).where(Role.name.in_(["cashier", "manager", "admin", "owner"]))
    if role:
        stmt = stmt.where(Role.name == role)
    return list(db.scalars(stmt.order_by(User.id.desc())).all())


def create_staff(
    db: Session,
    actor: User,
    name: str,
    email: str,
    password: str,
    role_name: str,
    phone: str | None = None,
) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise ValueError(f"Email '{email}' is already registered.")

    role_obj = get_role_by_name(db, role_name)
    if not role_obj:
        # Create role if missing in test db
        role_obj = Role(name=role_name, description=f"{role_name.capitalize()} role")
        db.add(role_obj)
        db.flush()

    staff_user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role_id=role_obj.id,
        status="active",
    )
    db.add(staff_user)
    db.flush()

    log_action(
        db,
        user_id=actor.id if actor else None,
        action="staff.create",
        entity_type="user",
        entity_id=staff_user.id,
        new_data={"email": email, "role": role_name},
    )
    db.commit()
    db.refresh(staff_user)
    return staff_user


def update_staff(
    db: Session,
    actor: User,
    staff_id: int,
    name: str | None = None,
    phone: str | None = None,
    role_name: str | None = None,
    status: str | None = None,
) -> User:
    staff_user = db.get(User, staff_id)
    if not staff_user or not staff_user.role or staff_user.role.name not in ["cashier", "manager", "admin", "owner"]:
        raise ValueError("Staff user not found.")

    old_data = {"name": staff_user.name, "role": staff_user.role.name, "status": staff_user.status}

    if name is not None:
        staff_user.name = name
    if phone is not None:
        staff_user.phone = phone
    if status is not None:
        staff_user.status = status
    if role_name is not None:
        role_obj = get_role_by_name(db, role_name)
        if not role_obj:
            role_obj = Role(name=role_name, description=f"{role_name.capitalize()} role")
            db.add(role_obj)
            db.flush()
        staff_user.role_id = role_obj.id

    log_action(
        db,
        user_id=actor.id if actor else None,
        action="staff.update",
        entity_type="user",
        entity_id=staff_user.id,
        old_data=old_data,
        new_data={"name": staff_user.name, "role": role_name, "status": staff_user.status},
    )
    db.commit()
    db.refresh(staff_user)
    return staff_user
