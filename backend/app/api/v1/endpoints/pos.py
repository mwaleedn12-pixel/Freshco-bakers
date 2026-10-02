"""
Phase 2 POS & Counter Billing Endpoints.
Accessible by Cashier, Manager, Admin, Owner.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import OrderOut
from app.schemas.pos import POSDailyClosing, POSReturnCreate, POSSaleCreate
from app.services import pos_service

router = APIRouter()


@router.get("/barcode/{code}")
def lookup_barcode(
    code: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("cashier", "manager", "admin", "owner")),
) -> dict[str, Any]:
    product = pos_service.lookup_barcode(db, code)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No product found for barcode '{code}'")
    return {
        "id": product.id,
        "sku": product.sku,
        "barcode": product.barcode,
        "name": product.name,
        "price": float(product.price),
        "sale_price": float(product.sale_price) if product.sale_price else None,
        "status": product.status,
    }


@router.post("/sales", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_pos_sale(
    payload: POSSaleCreate,
    db: Session = Depends(get_db),
    cashier: User = Depends(require_roles("cashier", "manager", "admin", "owner")),
) -> OrderOut:
    items_data = [item.model_dump() for item in payload.items]
    try:
        order = pos_service.create_pos_sale(
            db,
            cashier=cashier,
            branch_id=payload.branch_id,
            customer_id=payload.customer_id,
            items_data=items_data,
            payment_method_str=payload.payment_method,
            amount_paid=payload.amount_paid,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return OrderOut.model_validate(order)


@router.post("/returns")
def process_pos_return(
    payload: POSReturnCreate,
    db: Session = Depends(get_db),
    cashier: User = Depends(require_roles("cashier", "manager", "admin", "owner")),
) -> dict[str, Any]:
    items = [item.model_dump() for item in payload.items]
    try:
        return_obj = pos_service.process_pos_return(
            db, cashier=cashier, order_id=payload.order_id, items_to_return=items
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "id": return_obj.id,
        "order_id": return_obj.order_id,
        "refund_amount": float(return_obj.refund_amount) if return_obj.refund_amount else 0.0,
        "status": return_obj.status,
    }


@router.post("/closing")
def daily_cash_closing(
    payload: POSDailyClosing,
    db: Session = Depends(get_db),
    cashier: User = Depends(require_roles("cashier", "manager", "admin", "owner")),
) -> dict[str, Any]:
    return {
        "cashier_id": cashier.id,
        "cashier_name": cashier.name,
        "branch_id": payload.branch_id,
        "cash_in_drawer": payload.cash_in_drawer,
        "card_total": payload.card_total,
        "total_reconciled": payload.cash_in_drawer + payload.card_total,
        "notes": payload.notes,
        "timestamp": cashier.created_at.isoformat() if cashier.created_at else None,
    }
