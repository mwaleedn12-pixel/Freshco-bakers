"""
In-app notifications. `notify*` helpers only add rows to the caller's transaction (the caller commits).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import Role, User

STAFF_ROLES = ("manager", "admin", "owner")


def notify(db: Session, user_id: int | None, title: str, message: str | None = None, type: str = "general") -> None:
    if user_id is None:
        return
    db.add(Notification(user_id=user_id, title=title, message=message, type=type))


def notify_staff(db: Session, title: str, message: str | None = None, type: str = "general") -> None:
    staff = (
        db.query(User.id)
        .join(Role, User.role_id == Role.id)
        .filter(Role.name.in_(STAFF_ROLES), User.status == "active")
        .all()
    )
    for (user_id,) in staff:
        db.add(Notification(user_id=user_id, title=title, message=message, type=type))
