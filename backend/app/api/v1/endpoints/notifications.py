from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationOut, NotificationPage
from app.services.errors import ServiceError

router = APIRouter()


def _unread(db: Session, user: User) -> int:
    return db.query(func.count(Notification.id)).filter(
        Notification.user_id == user.id, Notification.is_read.is_(False)).scalar()


@router.get("", response_model=NotificationPage)
def list_notifications(
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    total = q.count()
    items = q.order_by(Notification.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return NotificationPage(items=items, total=total, unread_count=_unread(db, user), page=page, limit=limit)


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return {"unread_count": _unread(db, user)}


@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read.is_(False)).update(
        {"is_read": True})
    db.commit()
    return {"unread_count": 0}


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    note = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    if note is None:
        raise ServiceError("Notification not found", 404)
    note.is_read = True
    db.commit()
    db.refresh(note)
    return note
