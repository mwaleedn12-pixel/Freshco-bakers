from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart, CartItem
from app.models.catalog import Product
from app.models.user import User
from app.schemas.cart import CartItemOut, CartOut
from app.services.errors import ServiceError
from app.services.pricing import effective_price, q2

MAX_QTY = 100


def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).options(selectinload(Cart.items)).filter(Cart.customer_id == user.id).first()
    if cart is None:
        cart = Cart(customer_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def build_cart_out(db: Session, cart: Cart) -> CartOut:
    ids = [i.product_id for i in cart.items]
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(ids))} if ids else {}
    items: list[CartItemOut] = []
    subtotal = Decimal("0")
    for item in cart.items:
        product = products.get(item.product_id)
        price = effective_price(product) if product else q2(item.unit_price)
        line = q2(price * item.quantity)
        subtotal += line
        items.append(CartItemOut(
            id=item.id, product_id=item.product_id,
            product_name=product.name if product else "Unavailable product",
            unit_price=float(price), quantity=item.quantity, line_total=float(line),
            is_available=bool(product and product.status == "active" and product.is_available),
        ))
    return CartOut(id=cart.id, items=items, item_count=sum(i.quantity for i in cart.items), subtotal=float(subtotal))


def add_item(db: Session, user: User, product_id: int, quantity: int) -> Cart:
    product = db.get(Product, product_id)
    if product is None or product.status != "active":
        raise ServiceError("Product not found", 404)
    if not product.is_available:
        raise ServiceError(f"{product.name} is currently unavailable", 400)
    cart = get_or_create_cart(db, user)
    existing = next((i for i in cart.items if i.product_id == product_id), None)
    if existing:
        existing.quantity = min(existing.quantity + quantity, MAX_QTY)
        existing.unit_price = effective_price(product)
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity,
                        unit_price=effective_price(product)))
    db.commit()
    db.expire_all()
    return get_or_create_cart(db, user)


def _get_item(db: Session, cart: Cart, item_id: int) -> CartItem:
    item = next((i for i in cart.items if i.id == item_id), None)
    if item is None:
        raise ServiceError("Cart item not found", 404)
    return item


def update_item(db: Session, user: User, item_id: int, quantity: int) -> Cart:
    cart = get_or_create_cart(db, user)
    _get_item(db, cart, item_id).quantity = quantity
    db.commit()
    db.expire_all()
    return get_or_create_cart(db, user)


def remove_item(db: Session, user: User, item_id: int) -> Cart:
    cart = get_or_create_cart(db, user)
    item = _get_item(db, cart, item_id)
    cart.items.remove(item)
    db.commit()
    db.expire_all()
    return get_or_create_cart(db, user)


def clear_cart(db: Session, user: User) -> Cart:
    cart = get_or_create_cart(db, user)
    cart.items.clear()
    db.commit()
    db.expire_all()
    return get_or_create_cart(db, user)
