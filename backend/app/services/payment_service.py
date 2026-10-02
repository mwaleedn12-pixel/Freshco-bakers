"""
Payment Processing & Thermal Receipt Generator Service.
Handles CASH, CARD, ONLINE (JazzCash / EasyPaisa / Stripe), and WALLET transactions.
"""
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, Payment, PaymentMethod, PaymentStatus
from app.models.setting import Setting
from app.services.audit_service import log_action


def process_payment(
    db: Session,
    order_id: int,
    method_str: str,
    amount: float,
    transaction_reference: str | None = None,
    actor_id: int | None = None,
) -> Payment:
    order = db.get(Order, order_id)
    if not order:
        raise ValueError("Order not found")

    method_enum = PaymentMethod(method_str.upper())
    now_iso = datetime.now(timezone.utc).isoformat()

    payment = Payment(
        order_id=order.id,
        method=method_enum,
        amount=amount,
        transaction_reference=transaction_reference or f"TXN-{order.id}-{int(datetime.now().timestamp())}",
        status=PaymentStatus.PAID,
        paid_at=now_iso,
    )
    db.add(payment)
    db.flush()

    # Update order payment status
    total_paid = sum(p.amount for p in order.payments if p.status == PaymentStatus.PAID) + amount
    if total_paid >= order.total:
        order.payment_status = PaymentStatus.PAID
    else:
        order.payment_status = PaymentStatus.PARTIALLY_PAID

    log_action(
        db,
        user_id=actor_id,
        action="payment.process",
        entity_type="payment",
        entity_id=payment.id,
        new_data={"order_id": order.id, "amount": amount, "method": method_str},
    )
    db.commit()
    db.refresh(payment)
    return payment


def get_order_receipt(db: Session, order_id: int) -> dict[str, Any]:
    order = db.query(Order).options(joinedload(Order.items), joinedload(Order.payments)).filter(Order.id == order_id).first()
    if not order:
        raise ValueError("Order not found")

    bakery_setting = db.scalar(select(Setting).where(Setting.key == "bakery.name"))
    bakery_name = bakery_setting.value if bakery_setting else "Freshco Bakers"

    paid_payment = next((p for p in order.payments if p.status == PaymentStatus.PAID), None)

    return {
        "bakery_name": str(bakery_name),
        "order_number": order.order_number,
        "order_source": order.order_source.value if hasattr(order.order_source, "value") else str(order.order_source),
        "order_type": order.order_type.value if hasattr(order.order_type, "value") else str(order.order_type),
        "created_at": order.created_at.isoformat() if order.created_at else "",
        "items": [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "total": float(item.total),
            }
            for item in order.items
        ],
        "subtotal": float(order.subtotal),
        "discount_total": float(order.discount_total),
        "tax_total": float(order.tax_total),
        "delivery_fee": float(order.delivery_fee),
        "total": float(order.total),
        "payment_status": order.payment_status.value if hasattr(order.payment_status, "value") else str(order.payment_status),
        "payment_method": paid_payment.method.value if paid_payment and hasattr(paid_payment.method, "value") else (str(paid_payment.method) if paid_payment else None),
    }
