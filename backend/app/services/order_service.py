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
import logging

from app.models.order import (
    Order, OrderItem, OrderSource, OrderStatus, OrderStatusHistory, OrderType,
    Payment, PaymentMethod, PaymentStatus,
)
from app.models.setting import Setting
from app.models.user import Role, User
from app.services import cart_service, inventory_service, webhook_service, whatsapp_service
from app.services.notification_service import notify, notify_staff
from app.services.errors import ServiceError
from app.services.pricing import effective_price, q2

logger = logging.getLogger("freshco.orders")
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


def _attach_whatsapp_url(db: Session, order: Order | None) -> None:
    if order is None:
        return
    try:
        cust_name = "Valued Customer"
        cust_phone = ""
        if order.customer_id:
            u = db.get(User, order.customer_id)
            if u:
                cust_name = u.name or cust_name
                cust_phone = u.phone or ""
        items_payload = [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            }
            for item in (order.items or [])
        ]
        addr_text = None
        if order.address_id:
            addr = db.get(Address, order.address_id)
            if addr:
                addr_text = ", ".join([p for p in [addr.line1, addr.city] if p])
        payment_method_str = "Cash on Delivery"
        if order.payments:
            pm = order.payments[0].method
            payment_method_str = pm.value if hasattr(pm, "value") else str(pm)
        order.whatsapp_url = whatsapp_service.build_whatsapp_order_link(
            order_number=order.order_number,
            customer_name=cust_name,
            customer_phone=cust_phone,
            items=items_payload,
            total_amount=float(order.total),
            payment_method=payment_method_str,
            delivery_address=addr_text,
        )
    except Exception as e:
        logger.debug("Could not attach whatsapp_url to order: %s", e)


def _load_order(db: Session, order_id: int) -> Order | None:
    order = (
        db.query(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.payments),
            selectinload(Order.status_history),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if order is not None:
        _attach_whatsapp_url(db, order)
    return order


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
    address = None
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

    if getattr(req, "customer_phone", None) and not user.phone:
        user.phone = req.customer_phone.strip()

    cart.items.clear()
    db.commit()

    # Trigger WhatsApp and Automation Notifications (non-blocking)
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
            addr_parts = [p for p in [address.line1, address.line2, address.city] if p]
            addr_text = ", ".join(addr_parts)

        cust_name = getattr(req, "customer_name", None) or user.name or "Customer"
        cust_phone = getattr(req, "customer_phone", None) or user.phone or ""

        whatsapp_service.send_whatsapp_order_notification(
            order_number=order.order_number,
            customer_name=cust_name,
            customer_phone=cust_phone,
            items=items_payload,
            total_amount=float(total),
            payment_method=getattr(req, "payment_method", "Cash on Delivery"),
            delivery_address=addr_text,
            order_id=order.id,
        )

        webhook_service.dispatch_order_created(
            order_id=order.id,
            order_number=order.order_number,
            customer_name=cust_name,
            customer_phone=cust_phone,
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
    except Exception as err:
        logger.error("Error dispatching order notification: %s", err)

    return _load_order(db, order.id)


def guest_checkout(db: Session, req) -> Order:
    """Processes checkout for unregistered guest customers without login."""
    if not req.items:
        raise ServiceError("Your cart is empty", 400)

    customer_phone = (req.customer_phone or "").strip()
    customer_name = (req.customer_name or "Guest Customer").strip()

    # Find or create a user profile for the guest so addresses and history persist cleanly
    user = None
    if customer_phone:
        user = db.query(User).filter(User.phone == customer_phone).first()
    if user is None:
        guest_email = f"guest_{customer_phone.replace('+', '')}_{uuid4().hex[:6]}@freshcobakers.local"
        cust_role = db.query(Role).filter(Role.name == "customer").first()
        from app.core.security import hash_password
        user = User(
            name=customer_name,
            email=guest_email,
            phone=customer_phone,
            password_hash=hash_password(uuid4().hex),
            role_id=cust_role.id if cust_role else None,
            status="active",
        )
        db.add(user)
        db.flush()
    else:
        if customer_name and customer_name != "Guest Customer":
            user.name = customer_name

    # Address
    address_id = None
    addr_text = getattr(req, "delivery_address", None)
    if req.order_type == OrderType.DELIVERY:
        if not addr_text:
            raise ServiceError("A delivery address is required for delivery orders", 400)
        address = Address(
            user_id=user.id,
            line1=addr_text,
            city="Rawalpindi",
            label="Delivery Address",
        )
        db.add(address)
        db.flush()
        address_id = address.id

    # Branch
    if getattr(req, "branch_id", None) is not None:
        branch = db.query(Branch).filter(Branch.id == req.branch_id, Branch.status == "active").first()
    else:
        branch = db.query(Branch).filter(Branch.status == "active").order_by(Branch.id).first()

    scheduled_at = None
    if getattr(req, "scheduled_at", None) is not None:
        when = _aware(req.scheduled_at)
        if when <= datetime.now(timezone.utc):
            raise ServiceError("Scheduled time must be in the future", 400)
        scheduled_at = when.isoformat()

    # Lines & stock check
    product_ids = [i.product_id for i in req.items]
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids))}
    lines: list[dict] = []
    subtotal = Decimal("0")

    for item in req.items:
        product = products.get(item.product_id)
        if product is None or product.status != "active" or not product.is_available:
            name = product.name if product else "A product in your cart"
            raise ServiceError(f"{name} is no longer available.", 400)
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
        total_line = q2(price * item.quantity)
        subtotal += total_line
        lines.append({"product": product, "quantity": item.quantity, "price": price, "total": total_line,
                      "inventory": inventory})

    discount, coupon = Decimal("0"), None
    if getattr(req, "coupon_code", None):
        coupon, discount = apply_coupon(db, req.coupon_code, user, subtotal)
    taxable = subtotal - discount
    tax = q2(taxable * _setting_number(db, "tax.rate_percent", "percent") / 100)
    delivery_fee = q2(_setting_number(db, "delivery.fee_flat", "amount")) if req.order_type == OrderType.DELIVERY else Decimal("0.00")
    total = q2(taxable + tax + delivery_fee)

    order = Order(
        order_number=f"TMP-{uuid4().hex[:20]}",
        customer_id=user.id,
        branch_id=branch.id if branch else None,
        order_source=OrderSource.WEBSITE,
        order_type=req.order_type,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.UNPAID,
        subtotal=q2(subtotal), discount_total=discount, tax_total=tax, delivery_fee=delivery_fee, total=total,
        address_id=address_id, scheduled_at=scheduled_at, notes=getattr(req, "notes", None),
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

    payment_method_enum = PaymentMethod.CASH
    if getattr(req, "payment_method", None) in ["ONLINE", "CARD"]:
        payment_method_enum = PaymentMethod.ONLINE

    db.add(Payment(order_id=order.id, method=payment_method_enum, amount=total, status=PaymentStatus.UNPAID))
    db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.PENDING, changed_by=user.id,
                              note="Guest order placed"))
    if coupon is not None:
        db.add(CouponUsage(coupon_id=coupon.id, order_id=order.id, customer_id=user.id))

    notify(db, user.id, "Order received", f"Your order {order.order_number} has been placed. Total: {total}.", "order")
    notify_staff(db, "New guest order", f"{order.order_number} - {customer_name} - total {total}", "order")
    db.commit()

    # Notifications
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

        whatsapp_service.send_whatsapp_order_notification(
            order_number=order.order_number,
            customer_name=customer_name,
            customer_phone=customer_phone,
            items=items_payload,
            total_amount=float(total),
            payment_method=getattr(req, "payment_method", "Cash on Delivery"),
            delivery_address=addr_text,
            order_id=order.id,
        )

        webhook_service.dispatch_order_created(
            order_id=order.id,
            order_number=order.order_number,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=user.email,
            order_source="WEBSITE",
            order_type=order.order_type.value if hasattr(order.order_type, "value") else str(order.order_type),
            items=items_payload,
            subtotal=float(subtotal),
            discount=float(discount),
            tax=float(tax),
            delivery_fee=float(delivery_fee),
            total_amount=float(total),
            payment_method=getattr(req, "payment_method", "CASH"),
            branch_name=branch.name if branch else "Main Bakery",
            delivery_address=addr_text,
            special_instructions=getattr(req, "notes", None),
        )
    except Exception as err:
        logger.error("Error dispatching guest order notification: %s", err)

    return _load_order(db, order.id)


def _can_view(user: User, order: Order) -> bool:
    role = user.role.name if user.role else None
    return order.customer_id == user.id or role in STAFF_ROLES


def get_order(db: Session, user: User, order_id: int) -> Order:
    order = _load_order(db, order_id)
    if order is None or not _can_view(user, order):
        raise ServiceError("Order not found", 404)
    return order


def get_order_by_number(db: Session, order_number: str) -> Order:
    """Public lookup by order number — used for guest order tracking."""
    order = (
        db.query(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.payments),
            selectinload(Order.status_history),
        )
        .filter(Order.order_number == order_number.strip().upper())
        .first()
    )
    if order is None:
        raise ServiceError("Order not found. Please check the order number.", 404)
    _attach_whatsapp_url(db, order)
    return order


def list_my_orders(db: Session, user: User, *, page: int, limit: int) -> tuple[list[Order], int]:
    q = (
        db.query(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.payments),
            selectinload(Order.status_history),
        )
        .filter(Order.customer_id == user.id)
    )
    total = q.count()
    items = q.order_by(Order.id.desc()).offset((page - 1) * limit).limit(limit).all()
    for it in items:
        _attach_whatsapp_url(db, it)
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
