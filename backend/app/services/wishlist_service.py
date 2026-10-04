"""
Customer wishlists — simple save-for-later list, separate from the cart.
"""
from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.models.catalog import Product
from app.models.user import User
from app.models.wishlist import Wishlist, WishlistItem
from app.services.errors import ServiceError


def _get_or_create(db: Session, user: User) -> Wishlist:
    wl = db.query(Wishlist).options(selectinload(Wishlist.items)).filter(Wishlist.customer_id == user.id).first()
    if wl is None:
        wl = Wishlist(customer_id=user.id)
        db.add(wl)
        db.commit()
        db.refresh(wl)
    return wl


def _to_out(db: Session, wl: Wishlist) -> list[dict]:
    ids = [i.product_id for i in wl.items]
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(ids))} if ids else {}
    out = []
    for item in wl.items:
        p = products.get(item.product_id)
        if p is None:
            continue
        primary_image = next((img.image_url for img in sorted(p.images, key=lambda i: i.sort_order) if img.is_primary), None)
        if primary_image is None and p.images:
            primary_image = p.images[0].image_url
        out.append({
            "id": item.id, "product_id": p.id, "product_name": p.name,
            "price": float(p.price), "sale_price": float(p.sale_price) if p.sale_price else None,
            "image_url": primary_image, "is_available": p.is_available and p.status == "active",
        })
    return out


def list_wishlist(db: Session, user: User) -> list[dict]:
    return _to_out(db, _get_or_create(db, user))


def add_item(db: Session, user: User, product_id: int) -> list[dict]:
    product = db.get(Product, product_id)
    if product is None:
        raise ServiceError("Product not found", 404)
    wl = _get_or_create(db, user)
    if not any(i.product_id == product_id for i in wl.items):
        db.add(WishlistItem(wishlist_id=wl.id, product_id=product_id))
        db.commit()
        db.expire_all()
        wl = _get_or_create(db, user)
    return _to_out(db, wl)


def remove_item(db: Session, user: User, item_id: int) -> list[dict]:
    wl = _get_or_create(db, user)
    item = next((i for i in wl.items if i.id == item_id), None)
    if item is None:
        raise ServiceError("Wishlist item not found", 404)
    db.delete(item)
    db.commit()
    db.expire_all()
    wl = _get_or_create(db, user)
    return _to_out(db, wl)
