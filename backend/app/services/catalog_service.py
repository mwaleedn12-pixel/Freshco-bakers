"""
Catalog service — categories, products, images. Every admin change writes an audit log.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from sqlalchemy import func

from app.models.catalog import Category, Product, ProductImage
from app.models.review import Review
from app.models.user import User
from app.services.audit_service import log_action, snapshot
from app.services.errors import ServiceError
from app.utils.slug import unique_slug


# ---------------------------------------------------------------- categories
def list_categories(db: Session, *, include_inactive: bool = False) -> list[Category]:
    q = db.query(Category)
    if not include_inactive:
        q = q.filter(Category.status == "active")
    return q.order_by(Category.sort_order, Category.name).all()


def get_category(db: Session, category_id: int) -> Category:
    cat = db.get(Category, category_id)
    if cat is None:
        raise ServiceError("Category not found", 404)
    return cat


def create_category(db: Session, *, user: User, data: dict) -> Category:
    if data.get("parent_id") is not None:
        get_category(db, data["parent_id"])  # 404 if parent missing
    cat = Category(slug=unique_slug(db, Category, data["name"]), **data)
    db.add(cat)
    db.flush()
    log_action(db, user_id=user.id, action="category.create", entity_type="Category",
               entity_id=cat.id, new_data=snapshot(cat))
    db.commit()
    db.refresh(cat)
    return cat


def update_category(db: Session, *, user: User, category_id: int, changes: dict) -> Category:
    cat = get_category(db, category_id)
    old = snapshot(cat)
    if "parent_id" in changes and changes["parent_id"] is not None:
        parent = get_category(db, changes["parent_id"])
        if parent.id == cat.id or parent.parent_id == cat.id:
            raise ServiceError("A category cannot be its own parent or child", 400)
    for key, value in changes.items():
        setattr(cat, key, value)
    log_action(db, user_id=user.id, action="category.update", entity_type="Category",
               entity_id=cat.id, old_data=old, new_data=snapshot(cat))
    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, *, user: User, category_id: int) -> None:
    cat = get_category(db, category_id)
    has_children = db.query(Category.id).filter(Category.parent_id == cat.id).first() is not None
    has_products = db.query(Product.id).filter(Product.category_id == cat.id).first() is not None
    if has_children or has_products:
        raise ServiceError("Category still has subcategories or products. Deactivate it instead.", 400)
    log_action(db, user_id=user.id, action="category.delete", entity_type="Category",
               entity_id=cat.id, old_data=snapshot(cat))
    db.delete(cat)
    db.commit()


# ------------------------------------------------------------------ products
def _check_prices(price, sale_price) -> None:
    if sale_price is not None and Decimal(str(sale_price)) >= Decimal(str(price)):
        raise ServiceError("sale_price must be lower than price", 400)


def _check_unique(db: Session, *, sku: str | None, barcode: str | None, exclude_id: int | None = None) -> None:
    if sku is not None:
        q = db.query(Product.id).filter(Product.sku == sku)
        if exclude_id:
            q = q.filter(Product.id != exclude_id)
        if q.first():
            raise ServiceError("A product with this SKU already exists", 409)
    if barcode:
        q = db.query(Product.id).filter(Product.barcode == barcode)
        if exclude_id:
            q = q.filter(Product.id != exclude_id)
        if q.first():
            raise ServiceError("A product with this barcode already exists", 409)


def _attach_ratings(db: Session, products: list[Product]) -> list[Product]:
    """Sets .average_rating / .review_count (plain attrs, not DB columns) from approved reviews."""
    ids = [p.id for p in products]
    if not ids:
        return products
    rows = (
        db.query(Review.product_id, func.avg(Review.rating), func.count(Review.id))
        .filter(Review.product_id.in_(ids), Review.status == "approved")
        .group_by(Review.product_id)
        .all()
    )
    stats = {pid: (float(avg), count) for pid, avg, count in rows}
    for p in products:
        avg, count = stats.get(p.id, (0.0, 0))
        p.average_rating = round(avg, 1)
        p.review_count = count
    return products


def get_product(db: Session, product_id: int, *, include_inactive: bool = False) -> Product:
    product = (
        db.query(Product).options(selectinload(Product.images)).filter(Product.id == product_id).first()
    )
    if product is None or (not include_inactive and product.status != "active"):
        raise ServiceError("Product not found", 404)
    _attach_ratings(db, [product])
    return product


def list_products(
    db: Session,
    *,
    category_id: int | None = None,
    search: str | None = None,
    featured: bool | None = None,
    include_inactive: bool = False,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Product], int]:
    q = db.query(Product).options(selectinload(Product.images))
    if not include_inactive:
        q = q.filter(Product.status == "active")
    if category_id is not None:
        child_ids = [r[0] for r in db.query(Category.id).filter(Category.parent_id == category_id).all()]
        q = q.filter(Product.category_id.in_([category_id, *child_ids]))
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(Product.name.ilike(like), Product.sku.ilike(like), Product.description.ilike(like)))
    if featured is not None:
        q = q.filter(Product.is_featured == featured)
    total = q.count()
    items = q.order_by(Product.is_featured.desc(), Product.name).offset((page - 1) * limit).limit(limit).all()
    _attach_ratings(db, items)
    return items, total


def create_product(db: Session, *, user: User, data: dict) -> Product:
    _check_prices(data["price"], data.get("sale_price"))
    _check_unique(db, sku=data["sku"], barcode=data.get("barcode"))
    if data.get("category_id") is not None:
        get_category(db, data["category_id"])
    product = Product(slug=unique_slug(db, Product, data["name"]), **data)
    db.add(product)
    db.flush()
    log_action(db, user_id=user.id, action="product.create", entity_type="Product",
               entity_id=product.id, new_data=snapshot(product))
    db.commit()
    return get_product(db, product.id, include_inactive=True)


def update_product(db: Session, *, user: User, product_id: int, changes: dict) -> Product:
    product = get_product(db, product_id, include_inactive=True)
    old = snapshot(product)
    _check_unique(db, sku=changes.get("sku"), barcode=changes.get("barcode"), exclude_id=product.id)
    if changes.get("category_id") is not None:
        get_category(db, changes["category_id"])
    new_price = changes.get("price", product.price)
    new_sale = changes["sale_price"] if "sale_price" in changes else product.sale_price
    _check_prices(new_price, new_sale)
    for key, value in changes.items():
        setattr(product, key, value)
    log_action(db, user_id=user.id, action="product.update", entity_type="Product",
               entity_id=product.id, old_data=old, new_data=snapshot(product))
    db.commit()
    return get_product(db, product.id, include_inactive=True)


def archive_product(db: Session, *, user: User, product_id: int) -> None:
    """'Delete' = archive. Old orders keep their name/price snapshots and the product row stays for history."""
    product = get_product(db, product_id, include_inactive=True)
    old = snapshot(product)
    product.status = "archived"
    product.is_available = False
    log_action(db, user_id=user.id, action="product.archive", entity_type="Product",
               entity_id=product.id, old_data=old, new_data=snapshot(product))
    db.commit()


def add_image(db: Session, *, user: User, product_id: int, data: dict) -> Product:
    product = get_product(db, product_id, include_inactive=True)
    make_primary = data["is_primary"] or len(product.images) == 0
    if make_primary:
        for img in product.images:
            img.is_primary = False
    db.add(ProductImage(product_id=product.id, image_url=data["image_url"],
                        sort_order=data["sort_order"], is_primary=make_primary))
    log_action(db, user_id=user.id, action="product.image_add", entity_type="Product",
               entity_id=product.id, new_data={"image_url": data["image_url"]})
    db.commit()
    db.expire_all()
    return get_product(db, product.id, include_inactive=True)


def remove_image(db: Session, *, user: User, product_id: int, image_id: int) -> Product:
    product = get_product(db, product_id, include_inactive=True)
    image = db.query(ProductImage).filter(ProductImage.id == image_id, ProductImage.product_id == product.id).first()
    if image is None:
        raise ServiceError("Image not found", 404)
    was_primary = image.is_primary
    db.delete(image)
    db.flush()
    if was_primary:
        nxt = db.query(ProductImage).filter(ProductImage.product_id == product.id).order_by(ProductImage.sort_order).first()
        if nxt:
            nxt.is_primary = True
    log_action(db, user_id=user.id, action="product.image_remove", entity_type="Product",
               entity_id=product.id, old_data={"image_id": image_id})
    db.commit()
    db.expire_all()
    return get_product(db, product.id, include_inactive=True)
