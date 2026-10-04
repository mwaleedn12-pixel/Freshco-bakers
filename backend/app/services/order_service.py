"""
Order service — checkout, listing, cancellation.

Business rules enforced here (never in the Flutter app):
- Prices come from the products table, never from the client.
- Order status and payment status are separate; new orders are PENDING / UNPAID.
- Stock is RESERVED at checkout (reserved_quantity) to prevent overselling, and released on cancellation.
  If a product has no inventory row for the branch, stock is treated as not-limited (the inventory
  module will let admins configure it).
- order_items keep a snapshot of product name + unit price.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.branch import Address, Branch
from app.models.catalog import Product
from app.models.coupon import Coupon, CouponType, CouponUsage
from app.models.inventory import Inventory
from app.models.order import (
    Order, OrderItem, OrderSource, OrderStatus, OrderStatusHistory, OrderType,
    Payment, PaymentMethod, PaymentStatus,
)
from app.models.setting import Setting
from app.models.user import User
from app.services import cart_service, inventory_service, webhook_service
from app.services.notification_service import notify, notify_staff
from app.services.errors import ServiceError
from app.services.pricing import effective_price, q2

STAFF_ROLES = {"cashier", "manager", "admin", "owner"}
CANCELLABLE = (OrderStatus.PENDING, OrderStatus.CONFIRMED)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _setting_number(db: Session, key: str, field: str) -> Decimal:
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting and isinstance(setting.value, dict) and field in setting.value:
        try:
            return Decimal(str(setting.value[field]))
        except Exception:
            pass
    return Decimal("0")


def _load_order(db: Session, order_id: int) -> Order | None:
    return (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.payments), selectinload(Order.status_history))
        .filter(Order.id == order_id)
        .first()
    )


def apply_coupon(db: Session, code: str, user: User, subtotal: Decimal) -> tuple[Coupon, Decimal]:
    coupon = db.query(Coupon).filter(func.upper(Coupon.code) == code.strip().upper()).first()
    if coupon is None or coupon.status != "active":
        raise ServiceError("Invalid or inactive coupon code", 400)
    now = datetime.now(timezone.utc)
    if _aware(coupon.starts_at) and _aware(coupon.starts_at) > now:
        raise ServiceError("This coupon is not active yet", 400)
    if _aware(coupon.expires_at) and _aware(coupon.expires_at) < now:
        raise ServiceError("This coupon has expired", 400)
    if coupon.min_order_amount is not None and subtotal < Decimal(str(coupon.min_order_amount)):
        raise ServiceError(f"Minimum order amount for this coupon is {coupon.min_order_amount}", 400)
    if coupon.usage_limit is not None:
        used = db.query(func.count(CouponUsage.id)).filter(CouponUsage.coupon_id == coupon.id).scalar()
        if used >= coupon.usage_limit:
            raise ServiceError("This coupon has reached its usage limit", 400)
    if coupon.per_customer_limit is not None:
        used_by_user = db.query(func.count(CouponUsage.id)).filter(
            CouponUsage.coupon_id == coupon.id, CouponUsage.customer_id == user.id).scalar()
        if used_by_user >= coupon.per_customer_limit:
            raise ServiceError("You have already used this coupon the maximum number of times", 400)
    value = Decimal(str(coupon.value))
    discount = q2(subtotal * value / 100) if coupon.type == CouponType.PERCENTAGE else q2(value)
    return coupon, min(discount, subtotal)


def checkout(db: Session, user: User, req) -> Order:
    cart = cart_service.get_or_create_cart(db, user)
    if not cart.items:
        raise ServiceError("Your cart is empty", 400)

    # If customer provided name / phone during checkout, update profile
    if getattr(req, "customer_phone", None) and req.customer_phone.strip():
        user.phone = req.customer_phone.strip()
    if getattr(req, "customer_name", None) and req.customer_name.strip():
        user.name = req.customer_name.strip()

    # --- address / branch / schedule
    address_id = None
    if req.order_type == OrderType.DELIVERY:
        if req.address_id is None:
            raise ServiceError("A delivery address is required for delivery orders", 400)
        address = db.query(Address).filter(Address.id == req.address_id, Address.user_id == user.id).first()
        if address is None:
            raise ServiceError("Address not found", 404)
        address_id = address.id

    if req.branch_id is not None:
        branch = db.query(Branch).filter(Branch.id == req.branch_id, Branch.status == "active").first()
        if branch is None:
            raise ServiceError("Branch not found", 404)
    else:
        branch = db.query(Branch).filter(Branch.status == "active").order_by(Branch.id).first()

    scheduled_at = None
    if req.scheduled_at is not None:
        when = _aware(req.scheduled_at)
        if when <= datetime.now(timezone.utc):
            raise ServiceError("Scheduled time must be in the future", 400)
        scheduled_at = when.isoformat()

    # --- lines, availability, stock check (rows locked on PostgreSQL to stop overselling races)
    product_ids = [i.product_id for i in cart.items]
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids))}
    lines: list[dict] = []
    subtotal = Decimal("0")
    for item in cart.items:
        product = products.get(item.product_id)
        if product is None or product.status != "active" or not product.is_available:
            name = product.name if product else "A product in your cart"
            raise ServiceError(f"{name} is no longer available. Please remove it from your cart.", 400)
        inventory = None
        if branch is not None and product.track_inventory:
            inventory = (
                db.query(Inventory)
                .filter(Inventory.product_id == product.id, Inventory.branch_id == branch.id)
                .with_for_update()
                .first()
            )
            if inventory is not None and inventory.quantity - inventory.reserved_quantity < item.quantity:
                available = max(0, inventory.quantity - inventory.reserved_quantity)
                raise ServiceError(f"Not enough stock for {product.name} (only {available} left)", 400)
        price = effective_price(product)
        total = q2(price * item.quantity)
        subtotal += total
        lines.append({"product": product, "quantity": item.quantity, "price": price, "total": total,
                      "inventory": inventory})

    # --- totals
    discount, coupon = Decimal("0"), None
    if req.coupon_code:
        coupon, discount = apply_coupon(db, req.coupon_code, user, subtotal)
    taxable = subtotal - discount
    tax = q2(taxable * _setting_number(db, "tax.rate_percent", "percent") / 100)
    delivery_fee = q2(_setting_number(db, "delivery.fee_flat", "amount")) if req.order_type == OrderType.DELIVERY else Decimal("0.00")
    total = q2(taxable + tax + delivery_fee)

    # --- create the order
    order = Order(
        order_number=f"TMP-{uuid4().hex[:20]}",
        customer_id=user.id,
        branch_id=branch.id if branch else None,
        order_source=OrderSource.WEBSITE,
        order_type=req.order_type,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.UNPAID,
        subtotal=q2(subtotal), discount_total=discount, tax_total=tax, delivery_fee=delivery_fee, total=total,
        address_id=address_id, scheduled_at=scheduled_at, notes=req.notes,
    )
    db.add(order)
    db.flush()
    order.order_number = f"FB-{order.id:06d}"

    for line in lines:
        db.add(OrderItem(order_id=order.id, product_id=line["product"].id, product_name=line["product"].name,
                         unit_price=line["price"], quantity=line["quantity"], discount=Decimal("0.00"),
                         total=line["total"]))
        if line["inventory"] is not None:
            line["inventory"].reserved_quantity += line["quantity"]
    db.add(Payment(order_id=order.id, method=PaymentMethod(req.payment_method), amount=total,
                   status=PaymentStatus.UNPAID))
    db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.PENDING, changed_by=user.id,
                              note="Order placed"))
    if coupon is not None:
        db.add(CouponUsage(coupon_id=coupon.id, order_id=order.id, customer_id=user.id))

    notify(db, user.id, "Order received", f"Your order {order.order_number} has been placed. Total: {total}.", "order")
    notify_staff(db, "New order", f"{order.order_number} - {user.name} - total {total}", "order")

    cart.items.clear()
    db.commit()

    # Trigger n8n Automation Webhook (non-blocking)
    try:
        items_payload = [
            {
                "product_id": item_line["product"].id,
                "name": item_line["product"].name,
                "quantity": item_line["quantity"],
                "unit_price": float(item_line["price"]),
                "total": float(item_line["total"]),
            }
            for item_line in lines
        ]
        addr_text = None
        if address:
            addr_parts = [p for p in [address.recipient_name or user.name, address.street_address, address.area, address.city] if p]
            addr_text = ", ".join(addr_parts)

        webhook_service.dispatch_order_created(
            order_id=order.id,
            order_number=order.order_number,
            customer_name=user.name or "Customer",
            customer_phone=user.phone or "",
            customer_email=user.email,
            order_source=order.order_source.value if hasattr(order.order_source, "value") else str(order.order_source),
            order_type=order.order_type.value if hasattr(order.order_type, "value") else str(order.order_type),
            items=items_payload,
            subtotal=float(subtotal),
            discount=float(discount),
            tax=float(tax),
            delivery_fee=float(delivery_fee),
            total_amount=float(total),
            payment_method=req.payment_method,
            branch_name=branch.name if branch else "Main Bakery",
            delivery_address=addr_text,
            special_instructions=req.notes,
        )
    except Exception:
        pass

    return _load_order(db, order.id)


def _can_view(user: User, order: Order) -> bool:
    role = user.role.name if user.role else None
    return order.customer_id == user.id or role in STAFF_ROLES


def get_order(db: Session, user: User, order_id: int) -> Order:
    order = _load_order(db, order_id)
    if order is None or not _can_view(user, order):
        raise ServiceError("Order not found", 404)
    return order


def list_my_orders(db: Session, user: User, *, page: int, limit: int) -> tuple[list[Order], int]:
    q = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.payments))
        .filter(Order.customer_id == user.id)
    )
    total = q.count()
    items = q.order_by(Order.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total


def cancel_order(db: Session, user: User, order_id: int) -> Order:
    order = _load_order(db, order_id)
    if order is None or order.customer_id != user.id:
        raise ServiceError("Order not found", 404)
    if order.status not in CANCELLABLE:
        raise ServiceError("This order can no longer be cancelled", 400)

    inventory_service.release_reservation(db, order)

    order.status = OrderStatus.CANCELLED
    db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.CANCELLED, changed_by=user.id,
                              note="Cancelled by customer"))
    db.query(CouponUsage).filter(CouponUsage.order_id == order.id).delete()
    notify_staff(db, "Order cancelled", f"{order.order_number} was cancelled by the customer", "order")
    db.commit()
    db.expire_all()
    return _load_order(db, order.id)
