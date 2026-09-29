from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.branch import Branch
from app.models.catalog import Product
from app.models.inventory import Inventory
from app.models.user import User
from app.schemas.inventory import (
    InventoryOut, InventoryPage, MinimumUpdate, StockAdjust, StockTransfer, TransactionPage,
)
from app.services import inventory_service

router = APIRouter()
staff = require_roles("manager", "admin", "owner")


def _out(db: Session, inv: Inventory) -> InventoryOut:
    product = db.get(Product, inv.product_id)
    branch = db.get(Branch, inv.branch_id)
    return _build(inv, product, branch)


def _build(inv: Inventory, product: Product, branch: Branch) -> InventoryOut:
    available = inv.quantity - inv.reserved_quantity
    return InventoryOut(
        product_id=inv.product_id, product_name=product.name, sku=product.sku,
        branch_id=inv.branch_id, branch_name=branch.name,
        quantity=inv.quantity, reserved_quantity=inv.reserved_quantity, available_quantity=available,
        minimum_quantity=inv.minimum_quantity, is_low=available <= inv.minimum_quantity,
    )


@router.get("", response_model=InventoryPage)
def list_inventory(
    branch_id: int | None = None,
    low_stock: bool = False,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(staff),
):
    rows, total = inventory_service.list_inventory(db, branch_id=branch_id, low_stock=low_stock, search=search,
                                                   page=page, limit=limit)
    return InventoryPage(items=[_build(i, p, b) for i, p, b in rows], total=total, page=page, limit=limit)


@router.post("/adjust", response_model=InventoryOut)
def adjust_stock(payload: StockAdjust, db: Session = Depends(get_db), user: User = Depends(staff)):
    inv = inventory_service.adjust(db, user=user, product_id=payload.product_id, branch_id=payload.branch_id,
                                   type_=payload.type, quantity=payload.quantity)
    return _out(db, inv)


@router.post("/transfer", response_model=list[InventoryOut])
def transfer_stock(payload: StockTransfer, db: Session = Depends(get_db), user: User = Depends(staff)):
    source, target = inventory_service.transfer(
        db, user=user, product_id=payload.product_id, from_branch_id=payload.from_branch_id,
        to_branch_id=payload.to_branch_id, quantity=payload.quantity)
    return [_out(db, source), _out(db, target)]


@router.patch("/{product_id}/{branch_id}/minimum", response_model=InventoryOut)
def set_minimum(product_id: int, branch_id: int, payload: MinimumUpdate, db: Session = Depends(get_db),
                user: User = Depends(staff)):
    inv = inventory_service.set_minimum(db, user=user, product_id=product_id, branch_id=branch_id,
                                        minimum=payload.minimum_quantity)
    return _out(db, inv)


@router.get("/transactions", response_model=TransactionPage)
def list_transactions(
    product_id: int | None = None,
    branch_id: int | None = None,
    type: str | None = Query(default=None, pattern="^(PURCHASE|SALE|ADJUSTMENT|WASTE|RETURN|TRANSFER_IN|TRANSFER_OUT)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(staff),
):
    rows, total = inventory_service.list_transactions(db, product_id=product_id, branch_id=branch_id, type_=type,
                                                      page=page, limit=limit)
    return TransactionPage(items=rows, total=total, page=page, limit=limit)
