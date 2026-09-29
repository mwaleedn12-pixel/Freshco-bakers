from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.coupon import Coupon, CouponType, CouponUsage
from app.models.user import User
from app.services import order_service
from app.services.audit_service import log_action, snapshot
from app.services.errors import ServiceError
from app.services.pricing import q2


def times_used(db: Session, coupon_id: int) -> int:
    return db.query(func.count(CouponUsage.id)).filter(CouponUsage.coupon_id == coupon_id).scalar() or 0


def get_coupon(db: Session, coupon_id: int) -> Coupon:
    coupon = db.get(Coupon, coupon_id)
    if coupon is None:
        raise ServiceError("Coupon not found", 404)
    return coupon


def list_coupons(db: Session, *, status: str | None) -> list[Coupon]:
    q = db.query(Coupon)
    if status:
        q = q.filter(Coupon.status == status)
    return q.order_by(Coupon.id.desc()).all()


def create_coupon(db: Session, *, user: User, data: dict) -> Coupon:
    if db.query(Coupon.id).filter(func.upper(Coupon.code) == data["code"]).first():
        raise ServiceError("A coupon with this code already exists", 409)
    coupon = Coupon(**data)
    db.add(coupon)
    db.flush()
    log_action(db, user_id=user.id, action="coupon.create", entity_type="Coupon", entity_id=coupon.id,
               new_data=snapshot(coupon))
    db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(db: Session, *, user: User, coupon_id: int, changes: dict) -> Coupon:
    coupon = get_coupon(db, coupon_id)
    old = snapshot(coupon)
    for key, value in changes.items():
        setattr(coupon, key, value)
    if coupon.type == CouponType.PERCENTAGE and Decimal(str(coupon.value)) > 100:
        raise ServiceError("Percentage discount cannot be more than 100", 400)
    starts, expires = coupon.starts_at, coupon.expires_at
    if starts and expires and expires.replace(tzinfo=None) <= starts.replace(tzinfo=None):
        raise ServiceError("expires_at must be after starts_at", 400)
    log_action(db, user_id=user.id, action="coupon.update", entity_type="Coupon", entity_id=coupon.id,
               old_data=old, new_data=snapshot(coupon))
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, *, user: User, coupon_id: int) -> None:
    coupon = get_coupon(db, coupon_id)
    if times_used(db, coupon.id) > 0:
        raise ServiceError("This coupon has been used already. Deactivate it instead of deleting.", 400)
    log_action(db, user_id=user.id, action="coupon.delete", entity_type="Coupon", entity_id=coupon.id,
               old_data=snapshot(coupon))
    db.delete(coupon)
    db.commit()


def validate(db: Session, *, user: User, code: str, subtotal: float) -> tuple[Coupon, Decimal, Decimal]:
    """Preview for the cart screen. Uses the exact same rules as checkout."""
    sub = q2(subtotal)
    coupon, discount = order_service.apply_coupon(db, code, user, sub)
    return coupon, discount, q2(sub - discount)
