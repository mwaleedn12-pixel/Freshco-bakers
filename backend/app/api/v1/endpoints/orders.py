from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.order import OrderSource, OrderStatus, OrderType, PaymentStatus
from app.models.user import User
from app.schemas.order import (
    CheckoutRequest, OrderAdminDetailOut, OrderAdminOut, OrderAdminPage, OrderDetailOut, OrderOut, OrderPage,
    PaymentUpdate, StatusChange,
)
from app.services import order_admin_service, order_service

router = APIRouter()
staff = require_roles("manager", "admin", "owner")


def _admin_out(order, customer) -> OrderAdminOut:
    return OrderAdminOut(**OrderOut.model_validate(order).model_dump(),
                         customer_name=customer.name if customer else None,
                         customer_phone=customer.phone if customer else None,
                         customer_email=customer.email if customer else None)


def _admin_detail(db: Session, order_id: int) -> OrderAdminDetailOut:
    order, customer, address = order_admin_service.get_order_detail(db, order_id)
    base = OrderDetailOut.model_validate(order).model_dump()
    return OrderAdminDetailOut(**base,
                               customer_name=customer.name if customer else None,
                               customer_phone=customer.phone if customer else None,
                               customer_email=customer.email if customer else None,
                               address=address)


# ------------------------------------------------------------------ customer
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


# --------------------------------------------------------------------- staff
@router.get("/admin/list", response_model=OrderAdminPage)
def admin_list_orders(
    status: OrderStatus | None = None,
    payment_status: PaymentStatus | None = None,
    order_source: OrderSource | None = None,
    order_type: OrderType | None = None,
    branch_id: int | None = None,
    search: str | None = Query(default=None, max_length=100, description="order number, customer name/phone/email"),
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(staff),
):
    orders, customers, total = order_admin_service.list_orders(
        db, status=status, payment_status=payment_status, source=order_source, order_type=order_type,
        branch_id=branch_id, search=search, date_from=date_from, date_to=date_to, page=page, limit=limit)
    return OrderAdminPage(items=[_admin_out(o, customers.get(o.customer_id)) for o in orders],
                          total=total, page=page, limit=limit)


@router.get("/admin/{order_id}", response_model=OrderAdminDetailOut)
def admin_get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    return _admin_detail(db, order_id)


@router.patch("/{order_id}/status", response_model=OrderAdminDetailOut)
def change_status(order_id: int, payload: StatusChange, db: Session = Depends(get_db),
                  user: User = Depends(staff)):
    order_admin_service.change_status(db, user=user, order_id=order_id, new_status=payload.status,
                                      note=payload.note)
    return _admin_detail(db, order_id)


@router.patch("/{order_id}/payment", response_model=OrderAdminDetailOut)
def update_payment(order_id: int, payload: PaymentUpdate, db: Session = Depends(get_db),
                   user: User = Depends(staff)):
    order_admin_service.set_payment_status(db, user=user, order_id=order_id, new_status=payload.status,
                                           transaction_reference=payload.transaction_reference)
    return _admin_detail(db, order_id)


# ------------------------------------------------------- customer (by id)
@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return order_service.get_order(db, user, order_id)


@router.patch("/{order_id}/cancel", response_model=OrderDetailOut)
def cancel_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return order_service.cancel_order(db, user, order_id)
