"""
Customer Metrics & Management Service.
Calculates customer order stats, total spending, and repeat status.
"""
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order
from app.models.user import Role, User


def list_customers(db: Session, search: str | None = None) -> list[dict[str, Any]]:
    # Customers have role = 'customer' or role_id is None
    stmt = (
        select(
            User,
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(Order.total), 0.0).label("total_spend"),
        )
        .outerjoin(Role, User.role_id == Role.id)
        .outerjoin(Order, (Order.customer_id == User.id) & (Order.status != "cancelled"))
        .where((Role.name == "customer") | (User.role_id.is_(None)))
        .group_by(User.id)
        .order_by(User.id.desc())
    )

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where((User.name.ilike(pattern)) | (User.email.ilike(pattern)))

    results = db.execute(stmt).all()
    output = []
    for user, total_orders, total_spend in results:
        output.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "status": user.status,
            "total_orders": total_orders or 0,
            "total_spend": float(total_spend or 0.0),
            "created_at": user.created_at,
        })
    return output


def get_customer_detail(db: Session, customer_id: int) -> dict[str, Any] | None:
    user = db.query(User).options(joinedload(User.addresses)).filter(User.id == customer_id).first()
    if not user:
        return None

    order_stats = db.execute(
        select(
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(Order.total), 0.0).label("total_spend"),
        ).where(Order.customer_id == customer_id, Order.status != "cancelled")
    ).one()

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "status": user.status,
        "total_orders": order_stats.total_orders or 0,
        "total_spend": float(order_stats.total_spend or 0.0),
        "created_at": user.created_at,
        "addresses": user.addresses,
    }
