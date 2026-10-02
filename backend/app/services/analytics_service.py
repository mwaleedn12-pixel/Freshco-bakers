"""
Dashboard, Analytics & Business Intelligence Service (SRS Section 17).
Provides sales, channels, profit, top products, and operational KPI metrics.
"""
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.user import Role, User


def get_dashboard_summary(db: Session) -> dict[str, Any]:
    # Revenue total (paid non-cancelled orders)
    revenue = db.scalar(
        select(func.coalesce(func.sum(Order.total), 0.0)).where(
            Order.status != OrderStatus.CANCELLED, Order.payment_status == PaymentStatus.PAID
        )
    ) or 0.0

    # Total orders count
    total_orders = db.scalar(select(func.count(Order.id))) or 0

    # Pending orders count
    pending_orders = db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING)) or 0

    # Customers count
    total_customers = db.scalar(
        select(func.count(User.id)).outerjoin(Role, User.role_id == Role.id).where((Role.name == "customer") | (User.role_id.is_(None)))
    ) or 0

    # Low stock items count (inventory quantity <= minimum_quantity)
    low_stock_count = db.scalar(
        select(func.count(Inventory.id)).where(Inventory.quantity <= Inventory.minimum_quantity)
    ) or 0

    # Top 5 products by quantity sold
    top_products_q = (
        select(OrderItem.product_name, func.sum(OrderItem.quantity).label("sold_qty"))
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
    )
    top_products = [{"name": name, "sold_quantity": qty} for name, qty in db.execute(top_products_q).all()]

    return {
        "revenue": float(revenue),
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_customers": total_customers,
        "low_stock_count": low_stock_count,
        "top_products": top_products,
    }


def get_sales_channel_split(db: Session) -> dict[str, Any]:
    stmt = (
        select(Order.order_source, func.count(Order.id).label("order_count"), func.coalesce(func.sum(Order.total), 0.0).label("revenue"))
        .where(Order.status != OrderStatus.CANCELLED)
        .group_by(Order.order_source)
    )
    results = db.execute(stmt).all()
    channels = {}
    for source, count, rev in results:
        src_str = source.value if hasattr(source, "value") else str(source)
        channels[src_str] = {"orders": count, "revenue": float(rev)}
    return channels


def get_gross_profit_report(db: Session) -> dict[str, Any]:
    # Calculate revenue vs cost from order_items and product cost_price
    stmt = (
        select(
            func.coalesce(func.sum(OrderItem.total), 0.0).label("total_revenue"),
            func.coalesce(func.sum(OrderItem.quantity * Product.cost_price), 0.0).label("total_cost"),
        )
        .join(Product, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.status != OrderStatus.CANCELLED)
    )
    res = db.execute(stmt).one()
    rev = float(res.total_revenue or 0.0)
    cost = float(res.total_cost or 0.0)
    profit = rev - cost
    margin_pct = (profit / rev * 100.0) if rev > 0 else 0.0

    return {
        "total_revenue": rev,
        "total_cost": cost,
        "gross_profit": profit,
        "margin_percentage": round(margin_pct, 2),
    }
