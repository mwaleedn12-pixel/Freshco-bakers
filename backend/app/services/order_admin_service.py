"""
Staff-side order management (manager / admin / owner).

Allowed status flow (anything else is rejected):
  PENDING -> CONFIRMED -> PREPARING -> READY -> OUT_FOR_DELIVERY -> DELIVERED   (delivery orders)
                                          READY -> PICKED_UP                    (pickup orders)
  PENDING / CONFIRMED / PREPARING / READY -> CANCELLED  (releases the reserved stock)

Stock rule: reserved at checkout, consumed (SALE transaction) when the order is DELIVERED / PICKED_UP.
Cash orders are marked PAID automatically at that moment (cash collected on delivery / at the counter).
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.branch import Address
from app.models.coupon import CouponUsage
from app.models.order import (
    Order, OrderStatus as S, OrderStatusHistory, OrderType, PaymentMethod, PaymentStatus,
)
from app.models.user import User
from app.services import inventory_service, webhook_service
from app.services.audit_service import log_action
from app.services.errors import ServiceError
from app.services.notification_service import notify

TRANSITIONS: dict[S, set[S]] = {
    S.PENDING: {S.CONFIRMED, S.CANCELLED},
    S.CONFIRMED: {S.PREPARING, S.CANCELLED},
    S.PREPARING: {S.READY, S.CANCELLED},
    S.READY: {S.OUT_FOR_DELIVERY, S.PICKED_UP, S.CANCELLED},
    S.OUT_FOR_DELIVERY: {S.DELIVERED},
}

CUSTOMER_MESSAGES = {
    S.CONFIRMED: "has been confirmed",
    S.PREPARING: "is being prepared",
    S.READY: "is ready",
    S.OUT_FOR_DELIVERY: "is out for delivery",
    S.DELIVERED: "has been delivered. Enjoy!",
    S.PICKED_UP: "has been picked up. Enjoy!",
    S.CANCELLED: "was cancelled by the bakery",
}


def _load(db: Session, order_id: int) -> Order:
    order = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.payments), selectinload(Order.status_history))
        .filter(Order.id == order_id)
        .first()
    )
    if order is None:
        raise ServiceError("Order not found", 404)
    return order


def get_order_detail(db: Session, order_id: int):
    order = _load(db, order_id)
    customer = db.get(User, order.customer_id) if order.customer_id else None
    address = db.get(Address, order.address_id) if order.address_id else None
    return order, customer, address


def list_orders(db: Session, *, status: S | None, payment_status: PaymentStatus | None, source, order_type: OrderType | None,
                branch_id: int | None, search: str | None, date_from: date | None, date_to: date | None,
                page: int, limit: int):
    q = db.query(Order).options(selectinload(Order.items), selectinload(Order.payments)).outerjoin(
        User, Order.customer_id == User.id)
    if status:
        q = q.filter(Order.status == status)
    if payment_status:
        q = q.filter(Order.payment_status == payment_status)
    if source:
        q = q.filter(Order.order_source == source)
    if order_type:
        q = q.filter(Order.order_type == order_type)
    if branch_id is not None:
        q = q.filter(Order.branch_id == branch_id)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(Order.order_number.ilike(like), User.name.ilike(like), User.phone.ilike(like),
                         User.email.ilike(like)))
    if date_from:
        q = q.filter(Order.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        q = q.filter(Order.created_at < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc))
    total = q.count()
    orders = q.order_by(Order.id.desc()).offset((page - 1) * limit).limit(limit).all()
    ids = {o.customer_id for o in orders if o.customer_id}
    customers = {u.id: u for u in db.query(User).filter(User.id.in_(ids))} if ids else {}
    return orders, customers, total


def change_status(db: Session, *, user: User, order_id: int, new_status: S, note: str | None) -> Order:
    order = _load(db, order_id)
    if new_status not in TRANSITIONS.get(order.status, set()):
        raise ServiceError(f"Cannot change order from {order.status.value} to {new_status.value}", 400)
    if new_status in (S.OUT_FOR_DELIVERY, S.DELIVERED) and order.order_type != OrderType.DELIVERY:
        raise ServiceError("Only delivery orders can be sent out for delivery", 400)
    if new_status == S.PICKED_UP and order.order_type != OrderType.PICKUP:
        raise ServiceError("Only pickup orders can be marked as picked up", 400)

    old = order.status
    if new_status == S.CANCELLED:
        inventory_service.release_reservation(db, order)
        db.query(CouponUsage).filter(CouponUsage.order_id == order.id).delete()
    if new_status in (S.DELIVERED, S.PICKED_UP):
        inventory_service.complete_sale(db, order, user.id)
        if order.payment_status == PaymentStatus.UNPAID and order.payments and all(
                p.method == PaymentMethod.CASH for p in order.payments):
            order.payment_status = PaymentStatus.PAID
            for p in order.payments:
                p.status = PaymentStatus.PAID
                p.paid_at = datetime.now(timezone.utc).isoformat()

    order.status = new_status
    db.add(OrderStatusHistory(order_id=order.id, status=new_status, changed_by=user.id, note=note))
    notify(db, order.customer_id, f"Order {order.order_number}",
           f"Your order {order.order_number} {CUSTOMER_MESSAGES[new_status]}.", "order")
    log_action(db, user_id=user.id, action="order.status", entity_type="Order", entity_id=order.id,
               old_data={"status": old.value}, new_data={"status": new_status.value, "note": note})
    db.commit()
    db.expire_all()

    # Trigger n8n Automation Webhook (non-blocking)
    try:
        customer = db.get(User, order.customer_id) if order.customer_id else None
        webhook_service.dispatch_order_status_updated(
            order_id=order.id,
            order_number=order.order_number,
            old_status=old.value if hasattr(old, "value") else str(old),
            new_status=new_status.value if hasattr(new_status, "value") else str(new_status),
            customer_name=customer.name if customer else "Valued Customer",
            customer_phone=customer.phone if customer else None,
            customer_email=customer.email if customer else None,
            note=note,
        )
    except Exception:
        pass

    return _load(db, order_id)


def set_payment_status(db: Session, *, user: User, order_id: int, new_status: str,
                       transaction_reference: str | None) -> Order:
    order = _load(db, order_id)
    target = PaymentStatus(new_status)
    current = order.payment_status
    allowed = {
        PaymentStatus.PAID: {PaymentStatus.UNPAID, PaymentStatus.FAILED},
        PaymentStatus.FAILED: {PaymentStatus.UNPAID},
        PaymentStatus.REFUNDED: {PaymentStatus.PAID},
    }
    if current not in allowed[target]:
        raise ServiceError(f"Cannot change payment from {current.value} to {target.value}", 400)
    order.payment_status = target
    for p in order.payments:
        p.status = target
        if transaction_reference:
            p.transaction_reference = transaction_reference
        if target == PaymentStatus.PAID:
            p.paid_at = datetime.now(timezone.utc).isoformat()
    notify(db, order.customer_id, f"Payment for {order.order_number}",
           f"Payment status: {target.value}.", "payment")
    log_action(db, user_id=user.id, action="order.payment", entity_type="Order", entity_id=order.id,
               old_data={"payment_status": current.value}, new_data={"payment_status": target.value,
                                                                     "transaction_reference": transaction_reference})
    db.commit()
    db.expire_all()
    return _load(db, order_id)
