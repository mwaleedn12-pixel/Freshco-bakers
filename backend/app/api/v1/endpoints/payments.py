"""
Payment & Thermal Receipt Endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import PaymentOut, PaymentProcessRequest, ThermalReceiptOut
from app.services import payment_service

router = APIRouter()


@router.post("/process", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def process_payment(
    payload: PaymentProcessRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> PaymentOut:
    try:
        payment = payment_service.process_payment(
            db,
            order_id=payload.order_id,
            method_str=payload.method,
            amount=payload.amount,
            transaction_reference=payload.transaction_reference,
            actor_id=actor.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PaymentOut(
        id=payment.id,
        order_id=payment.order_id,
        method=payment.method.value if hasattr(payment.method, "value") else str(payment.method),
        amount=float(payment.amount),
        status=payment.status.value if hasattr(payment.status, "value") else str(payment.status),
        transaction_reference=payment.transaction_reference,
        created_at=payment.created_at,
    )


@router.get("/receipt/{order_id}", response_model=ThermalReceiptOut)
def get_receipt(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ThermalReceiptOut:
    try:
        receipt_data = payment_service.get_order_receipt(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ThermalReceiptOut(**receipt_data)
