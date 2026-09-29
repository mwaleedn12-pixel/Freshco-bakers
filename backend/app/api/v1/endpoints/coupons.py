from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.coupon import (
    CouponCreate, CouponOut, CouponUpdate, CouponValidateOut, CouponValidateRequest,
)
from app.services import coupon_service

router = APIRouter()
admin_only = require_roles("admin", "owner")


def _out(db: Session, coupon) -> CouponOut:
    out = CouponOut.model_validate(coupon)
    out.times_used = coupon_service.times_used(db, coupon.id)
    return out


@router.post("/validate", response_model=CouponValidateOut)
def validate_coupon(payload: CouponValidateRequest, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    """Customer: check a coupon against the cart subtotal before checkout."""
    coupon, discount, after = coupon_service.validate(db, user=user, code=payload.code, subtotal=payload.subtotal)
    return CouponValidateOut(code=coupon.code, discount_amount=float(discount), subtotal_after_discount=float(after))


@router.get("", response_model=list[CouponOut])
def list_coupons(status: str | None = None, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return [_out(db, c) for c in coupon_service.list_coupons(db, status=status)]


@router.post("", response_model=CouponOut, status_code=201)
def create_coupon(payload: CouponCreate, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return _out(db, coupon_service.create_coupon(db, user=user, data=payload.model_dump()))


@router.get("/{coupon_id}", response_model=CouponOut)
def get_coupon(coupon_id: int, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return _out(db, coupon_service.get_coupon(db, coupon_id))


@router.put("/{coupon_id}", response_model=CouponOut)
def update_coupon(coupon_id: int, payload: CouponUpdate, db: Session = Depends(get_db),
                  user: User = Depends(admin_only)):
    return _out(db, coupon_service.update_coupon(db, user=user, coupon_id=coupon_id,
                                                 changes=payload.model_dump(exclude_unset=True)))


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coupon(coupon_id: int, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    coupon_service.delete_coupon(db, user=user, coupon_id=coupon_id)
