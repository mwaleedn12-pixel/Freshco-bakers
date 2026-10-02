"""
Phase 2 POS & Billing Backend Service (SRS Section 7 & Section 10).
- POS sales write to central orders & order_items tables with order_source = POS.
- Creates real-time inventory transactions (OUT) rather than overwriting stock.
- Instant cash/card receipt & order completion.
"""
from datetime import datetime, timezone
import random
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.models.inventory import Inventory, InventoryTransaction, InventoryTransactionType
from app.models.order import (
    Order, OrderItem, OrderSource, OrderStatus, OrderStatusHistory, OrderType, Payment, PaymentMethod, PaymentStatus,
)
from app.models.return_ import Return
from app.models.user import User
from app.services.audit_service import log_action


def lookup_barcode(db: Session, barcode_or_sku: str) -> Product | None:
    return db.scalar(
        select(Product).where(
            (Product.barcode == barcode_or_sku) | (Product.sku == barcode_or_sku)
        )
    )


def create_pos_sale(
    db: Session,
    cashier: User,
    branch_id: int | None,
    customer_id: int | None,
    items_data: list[dict[str, Any]],
    payment_method_str: str,
    amount_paid: float,
    notes: str | None = None,
) -> Order:
    now_iso = datetime.now(timezone.utc).isoformat()
    order_num = f"POS-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

    order = Order(
        order_number=order_num,
        customer_id=customer_id,
        branch_id=branch_id,
        order_source=OrderSource.POS,
        order_type=OrderType.PICKUP,
        status=OrderStatus.DELIVERED,  # POS sale completed immediately on counter
        payment_status=PaymentStatus.PAID,
        notes=notes,
    )
    db.add(order)
    db.flush()

    subtotal = 0.0
    discount_total = 0.0

    for item in items_data:
        product_id = item["product_id"]
        qty = item["quantity"]
        disc = item.get("discount", 0.0)

        product = db.get(Product, product_id)
        if not product or product.status != "active":
            raise ValueError(f"Product ID {product_id} is unavailable for POS sale.")

        unit_price = float(product.sale_price if product.sale_price and product.sale_price > 0 else product.price)
        item_subtotal = unit_price * qty
        item_total = max(0.0, item_subtotal - disc)

        subtotal += item_subtotal
        discount_total += disc

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            unit_price=unit_price,
            quantity=qty,
            discount=disc,
            total=item_total,
        )
        db.add(order_item)

        # Record Inventory OUT Transaction & Deduct Stock
        if branch_id:
            inv = db.scalar(
                select(Inventory).where(
                    Inventory.product_id == product.id,
                    Inventory.branch_id == branch_id,
                )
            )
            if inv:
                inv.quantity = max(0, inv.quantity - qty)
                inv_tx = InventoryTransaction(
                    product_id=product.id,
                    branch_id=branch_id,
                    type=InventoryTransactionType.SALE,
                    quantity=-qty,
                    reference_type="POS_SALE",
                    reference_id=order.id,
                    created_by=cashier.id,
                )
                db.add(inv_tx)

    order.subtotal = subtotal
    order.discount_total = discount_total
    order.tax_total = round(subtotal * 0.05, 2)  # 5% tax
    order.total = subtotal - discount_total + order.tax_total

    # Add Payment Record
    pm = PaymentMethod(payment_method_str.upper())
    payment = Payment(
        order_id=order.id,
        method=pm,
        amount=amount_paid,
        status=PaymentStatus.PAID,
        paid_at=now_iso,
        transaction_reference=f"POS-CASHIER-{cashier.id}-{int(datetime.now().timestamp())}",
    )
    db.add(payment)

    # Status History
    hist = OrderStatusHistory(
        order_id=order.id,
        status=OrderStatus.DELIVERED,
        changed_by=cashier.id,
        note="POS Sale completed at counter",
    )
    db.add(hist)

    log_action(
        db,
        user_id=cashier.id,
        action="pos.sale",
        entity_type="order",
        entity_id=order.id,
        new_data={"order_number": order_num, "total": order.total, "payment_method": payment_method_str},
    )

    db.commit()
    db.refresh(order)
    return order


def process_pos_return(
    db: Session,
    cashier: User,
    order_id: int,
    items_to_return: list[dict[str, Any]],
) -> Return:
    order = db.get(Order, order_id)
    if not order:
        raise ValueError("Order not found.")

    total_refund = 0.0
    first_return = None

    for item in items_to_return:
        order_item_id = item["order_item_id"]
        qty = item["quantity"]
        reason = item.get("reason", "Customer return")

        o_item = db.get(OrderItem, order_item_id)
        if not o_item or o_item.order_id != order.id:
            raise ValueError(f"Order item {order_item_id} invalid for order {order_id}")

        unit_refund = float(o_item.total) / float(o_item.quantity)
        refund_amount = unit_refund * qty
        total_refund += refund_amount

        ret_obj = Return(
            order_id=order.id,
            order_item_id=o_item.id,
            quantity=qty,
            reason=reason,
            status="completed",
            refund_amount=refund_amount,
            created_by=cashier.id,
        )
        db.add(ret_obj)
        db.flush()

        if not first_return:
            first_return = ret_obj

        # Inventory RETURN Transaction (restock returned items)
        if o_item.product_id and order.branch_id:
            inv = db.scalar(
                select(Inventory).where(
                    Inventory.product_id == o_item.product_id,
                    Inventory.branch_id == order.branch_id,
                )
            )
            if inv:
                inv.quantity += qty
                inv_tx = InventoryTransaction(
                    product_id=o_item.product_id,
                    branch_id=order.branch_id,
                    type=InventoryTransactionType.RETURN,
                    quantity=qty,
                    reference_type="POS_RETURN",
                    reference_id=ret_obj.id,
                    created_by=cashier.id,
                )
                db.add(inv_tx)

    order.status = OrderStatus.REFUNDED

    log_action(
        db,
        user_id=cashier.id,
        action="pos.return",
        entity_type="return",
        entity_id=order.id,
        new_data={"order_id": order.id, "total_refund": total_refund},
    )

    db.commit()
    return first_return or Return(order_id=order.id, status="completed", refund_amount=0.0)

