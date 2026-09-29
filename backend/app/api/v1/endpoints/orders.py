from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import CheckoutRequest, OrderDetailOut, OrderPage
from app.services import order_service

router = APIRouter()


@router.post("", response_model=OrderDetailOut, status_code=status.HTTP_201_CREATED)
def checkout(payload: CheckoutRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Turns the current cart into an order (prices, coupon, tax, delivery fee and stock are decided here)."""
    return order_service.checkout(db, user, payload)


@router.get("", response_model=OrderPage)
def list_my_orders(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = order_service.list_my_orders(db, user, page=page, limit=limit)
    return OrderPage(items=items, total=total, page=page, limit=limit)


@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return order_service.get_order(db, user, order_id)


@router.patch("/{order_id}/cancel", response_model=OrderDetailOut)
def cancel_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return order_service.cancel_order(db, user, order_id)
