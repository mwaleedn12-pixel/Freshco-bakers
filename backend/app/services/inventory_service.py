"""
Inventory service — the ONLY place that changes stock.
Every change writes an InventoryTransaction (who, what, why); stock is never silently overwritten.
  quantity           = physical stock on hand
  reserved_quantity  = held for open orders (released on cancel, consumed on completion)
  available          = quantity - reserved_quantity
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.catalog import Product
from app.models.inventory import Inventory, InventoryTransaction, InventoryTransactionType as T
from app.models.order import Order
from app.models.user import User
from app.services.audit_service import log_action
from app.services.errors import ServiceError
from app.services.notification_service import notify_staff

SIGN = {T.PURCHASE: 1, T.RETURN: 1, T.WASTE: -1}  # ADJUSTMENT is signed by the caller


def _get_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise ServiceError("Product not found", 404)
    return product


def _get_branch(db: Session, branch_id: int) -> Branch:
    branch = db.get(Branch, branch_id)
    if branch is None:
        raise ServiceError("Branch not found", 404)
    return branch


def _row(db: Session, product_id: int, branch_id: int, *, create: bool) -> Inventory | None:
    inv = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id, Inventory.branch_id == branch_id)
        .with_for_update()
        .first()
    )
    if inv is None and create:
        inv = Inventory(product_id=product_id, branch_id=branch_id, quantity=0, reserved_quantity=0, minimum_quantity=0)
        db.add(inv)
        db.flush()
    return inv


def _record(db: Session, inv: Inventory, type_: T, delta: int, user_id: int | None,
            reference_type: str, reference_id: int | None = None) -> None:
    db.add(InventoryTransaction(product_id=inv.product_id, branch_id=inv.branch_id, type=type_, quantity=delta,
                                reference_type=reference_type, reference_id=reference_id, created_by=user_id))


def _low_stock_alert(db: Session, inv: Inventory) -> None:
    if inv.minimum_quantity > 0 and (inv.quantity - inv.reserved_quantity) <= inv.minimum_quantity:
        product = db.get(Product, inv.product_id)
        name = product.name if product else f"Product #{inv.product_id}"
        notify_staff(db, "Low stock", f"{name} is low: {inv.quantity - inv.reserved_quantity} available "
                                      f"(minimum {inv.minimum_quantity})", "low_stock")


# ---------------------------------------------------------------- admin actions
def adjust(db: Session, *, user: User, product_id: int, branch_id: int, type_: str, quantity: int) -> Inventory:
    tx_type = T(type_)
    _get_product(db, product_id)
    _get_branch(db, branch_id)
    if tx_type == T.ADJUSTMENT:
        if quantity == 0:
            raise ServiceError("Adjustment cannot be zero", 400)
        delta = quantity
    else:
        if quantity <= 0:
            raise ServiceError(f"Quantity must be greater than zero for {tx_type.value}", 400)
        delta = SIGN[tx_type] * quantity

    inv = _row(db, product_id, branch_id, create=True)
    old_qty = inv.quantity
    new_qty = old_qty + delta
    if new_qty < inv.reserved_quantity:
        raise ServiceError(
            f"Stock cannot go below the {inv.reserved_quantity} units reserved for open orders", 400)
    inv.quantity = new_qty
    _record(db, inv, tx_type, delta, user.id, "manual")
    log_action(db, user_id=user.id, action=f"inventory.{tx_type.value.lower()}", entity_type="Inventory",
               entity_id=inv.id, old_data={"quantity": old_qty}, new_data={"quantity": new_qty})
    if delta < 0:
        _low_stock_alert(db, inv)
    db.commit()
    db.refresh(inv)
    return inv


def transfer(db: Session, *, user: User, product_id: int, from_branch_id: int, to_branch_id: int,
             quantity: int) -> tuple[Inventory, Inventory]:
    if from_branch_id == to_branch_id:
        raise ServiceError("Source and destination branch must be different", 400)
    _get_product(db, product_id)
    _get_branch(db, from_branch_id)
    _get_branch(db, to_branch_id)
    source = _row(db, product_id, from_branch_id, create=False)
    available = 0 if source is None else source.quantity - source.reserved_quantity
    if available < quantity:
        raise ServiceError(f"Not enough available stock to transfer (available: {available})", 400)
    target = _row(db, product_id, to_branch_id, create=True)
    source.quantity -= quantity
    target.quantity += quantity
    _record(db, source, T.TRANSFER_OUT, -quantity, user.id, "transfer", to_branch_id)
    _record(db, target, T.TRANSFER_IN, quantity, user.id, "transfer", from_branch_id)
    log_action(db, user_id=user.id, action="inventory.transfer", entity_type="Inventory", entity_id=source.id,
               new_data={"product_id": product_id, "from": from_branch_id, "to": to_branch_id, "quantity": quantity})
    _low_stock_alert(db, source)
    db.commit()
    db.refresh(source)
    db.refresh(target)
    return source, target


def set_minimum(db: Session, *, user: User, product_id: int, branch_id: int, minimum: int) -> Inventory:
    _get_product(db, product_id)
    _get_branch(db, branch_id)
    inv = _row(db, product_id, branch_id, create=True)
    old = inv.minimum_quantity
    inv.minimum_quantity = minimum
    log_action(db, user_id=user.id, action="inventory.set_minimum", entity_type="Inventory", entity_id=inv.id,
               old_data={"minimum_quantity": old}, new_data={"minimum_quantity": minimum})
    db.commit()
    db.refresh(inv)
    return inv


# ------------------------------------------------------------- order lifecycle
def release_reservation(db: Session, order: Order) -> None:
    """Order cancelled: give the reserved units back."""
    if order.branch_id is None:
        return
    for item in order.items:
        if item.product_id is None:
            continue
        inv = _row(db, item.product_id, order.branch_id, create=False)
        if inv is not None:
            inv.reserved_quantity = max(0, inv.reserved_quantity - item.quantity)


def complete_sale(db: Session, order: Order, user_id: int | None) -> None:
    """Order delivered / picked up: consume the reservation and take the units out of stock (SALE transaction)."""
    if order.branch_id is None:
        return
    for item in order.items:
        if item.product_id is None:
            continue
        inv = _row(db, item.product_id, order.branch_id, create=False)
        if inv is None:
            continue
        inv.reserved_quantity = max(0, inv.reserved_quantity - item.quantity)
        inv.quantity = max(0, inv.quantity - item.quantity)
        _record(db, inv, T.SALE, -item.quantity, user_id, "order", order.id)
        _low_stock_alert(db, inv)


# ---------------------------------------------------------------------- queries
def list_inventory(db: Session, *, branch_id: int | None, low_stock: bool, search: str | None,
                   page: int, limit: int):
    q = (
        db.query(Inventory, Product, Branch)
        .join(Product, Inventory.product_id == Product.id)
        .join(Branch, Inventory.branch_id == Branch.id)
    )
    if branch_id is not None:
        q = q.filter(Inventory.branch_id == branch_id)
    if low_stock:
        q = q.filter((Inventory.quantity - Inventory.reserved_quantity) <= Inventory.minimum_quantity)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(Product.name.ilike(like) | Product.sku.ilike(like))
    total = q.count()
    rows = q.order_by(Product.name, Branch.name).offset((page - 1) * limit).limit(limit).all()
    return rows, total


def list_transactions(db: Session, *, product_id: int | None, branch_id: int | None, type_: str | None,
                      page: int, limit: int):
    q = db.query(InventoryTransaction)
    if product_id is not None:
        q = q.filter(InventoryTransaction.product_id == product_id)
    if branch_id is not None:
        q = q.filter(InventoryTransaction.branch_id == branch_id)
    if type_:
        q = q.filter(InventoryTransaction.type == T(type_))
    total = q.count()
    rows = q.order_by(InventoryTransaction.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return rows, total
