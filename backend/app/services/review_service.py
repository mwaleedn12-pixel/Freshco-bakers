"""
Reviews: only customers who actually received the product can review it (one review per product);
reviews stay 'pending' until staff approve them.
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewOut
from app.services.audit_service import log_action
from app.services.errors import ServiceError
from app.services.notification_service import notify_staff


def _to_out(review: Review, name: str | None, *, first_name_only: bool) -> ReviewOut:
    if name and first_name_only:
        name = name.split()[0]
    return ReviewOut(id=review.id, product_id=review.product_id, rating=review.rating, comment=review.comment,
                     status=review.status, customer_name=name, created_at=review.created_at)


def _with_names(db: Session, reviews: list[Review], *, first_name_only: bool) -> list[ReviewOut]:
    ids = {r.customer_id for r in reviews}
    names = {u.id: u.name for u in db.query(User).filter(User.id.in_(ids))} if ids else {}
    return [_to_out(r, names.get(r.customer_id), first_name_only=first_name_only) for r in reviews]


def create_review(db: Session, user: User, *, product_id: int, rating: int, comment: str | None) -> ReviewOut:
    product = db.get(Product, product_id)
    if product is None or product.status != "active":
        raise ServiceError("Product not found", 404)
    if db.query(Review.id).filter(Review.customer_id == user.id, Review.product_id == product_id).first():
        raise ServiceError("You have already reviewed this product", 409)
    order_id = (
        db.query(Order.id)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(Order.customer_id == user.id, OrderItem.product_id == product_id,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.PICKED_UP]))
        .order_by(Order.id.desc())
        .scalar()
    )
    if order_id is None:
        raise ServiceError("You can only review products from your delivered or picked-up orders", 403)
    review = Review(customer_id=user.id, product_id=product_id, order_id=order_id, rating=rating,
                    comment=comment, status="pending")
    db.add(review)
    notify_staff(db, "New review to moderate", f"{user.name} rated {product.name} {rating}/5", "review")
    db.commit()
    db.refresh(review)
    return _to_out(review, user.name, first_name_only=False)


def product_reviews(db: Session, product_id: int, *, page: int, limit: int) -> dict:
    product = db.get(Product, product_id)
    if product is None or product.status != "active":
        raise ServiceError("Product not found", 404)
    base = db.query(Review).filter(Review.product_id == product_id, Review.status == "approved")
    total = base.count()
    avg = db.query(func.avg(Review.rating)).filter(Review.product_id == product_id, Review.status == "approved").scalar()
    counts = dict(db.query(Review.rating, func.count(Review.id))
                  .filter(Review.product_id == product_id, Review.status == "approved")
                  .group_by(Review.rating).all())
    rows = base.order_by(Review.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "product_id": product_id,
        "average_rating": round(float(avg), 2) if avg is not None else 0.0,
        "review_count": total,
        "distribution": {str(n): counts.get(n, 0) for n in range(1, 6)},
        "items": _with_names(db, rows, first_name_only=True),
        "page": page, "limit": limit,
    }


def my_reviews(db: Session, user: User, *, page: int, limit: int):
    q = db.query(Review).filter(Review.customer_id == user.id)
    total = q.count()
    rows = q.order_by(Review.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return _with_names(db, rows, first_name_only=False), total


def admin_list(db: Session, *, status: str | None, product_id: int | None, page: int, limit: int):
    q = db.query(Review)
    if status:
        q = q.filter(Review.status == status)
    if product_id is not None:
        q = q.filter(Review.product_id == product_id)
    total = q.count()
    rows = q.order_by(Review.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return _with_names(db, rows, first_name_only=False), total


def moderate(db: Session, *, user: User, review_id: int, new_status: str) -> ReviewOut:
    review = db.get(Review, review_id)
    if review is None:
        raise ServiceError("Review not found", 404)
    old = review.status
    review.status = new_status
    log_action(db, user_id=user.id, action="review.moderate", entity_type="Review", entity_id=review.id,
               old_data={"status": old}, new_data={"status": new_status})
    db.commit()
    db.refresh(review)
    return _with_names(db, [review], first_name_only=False)[0]
