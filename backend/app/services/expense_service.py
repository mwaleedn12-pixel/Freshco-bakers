"""
Branch Expense & Net Profit Management Service.
"""
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.models.expense import Expense
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.services.audit_service import log_action


def create_expense(
    db: Session,
    actor: User,
    category: str,
    amount: float,
    expense_date: str,
    branch_id: int | None = None,
    description: str | None = None,
) -> Expense:
    expense = Expense(
        branch_id=branch_id,
        category=category,
        description=description,
        amount=amount,
        expense_date=expense_date,
        created_by=actor.id,
    )
    db.add(expense)
    db.flush()

    log_action(
        db,
        user_id=actor.id,
        action="expense.create",
        entity_type="expense",
        entity_id=expense.id,
        new_data={"category": category, "amount": amount, "branch_id": branch_id},
    )
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(db: Session, branch_id: int | None = None) -> list[Expense]:
    stmt = select(Expense).order_by(Expense.id.desc())
    if branch_id:
        stmt = stmt.where(Expense.branch_id == branch_id)
    return list(db.scalars(stmt).all())


def get_net_profit_summary(db: Session, branch_id: int | None = None) -> dict[str, Any]:
    # Revenue & Product cost
    order_stmt = (
        select(
            func.coalesce(func.sum(OrderItem.total), 0.0).label("revenue"),
            func.coalesce(func.sum(OrderItem.quantity * Product.cost_price), 0.0).label("cost"),
        )
        .join(Product, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.status != OrderStatus.CANCELLED)
    )
    if branch_id:
        order_stmt = order_stmt.where(Order.branch_id == branch_id)

    order_res = db.execute(order_stmt).one()
    revenue = float(order_res.revenue or 0.0)
    cost = float(order_res.cost or 0.0)
    gross_profit = revenue - cost

    # Expenses
    expense_stmt = select(func.coalesce(func.sum(Expense.amount), 0.0))
    if branch_id:
        expense_stmt = expense_stmt.where(Expense.branch_id == branch_id)
    total_expenses = float(db.scalar(expense_stmt) or 0.0)

    net_profit = gross_profit - total_expenses
    net_margin = (net_profit / revenue * 100.0) if revenue > 0 else 0.0

    return {
        "branch_id": branch_id,
        "revenue": revenue,
        "cost_of_goods": cost,
        "gross_profit": gross_profit,
        "operating_expenses": total_expenses,
        "net_profit": net_profit,
        "net_margin_percent": round(net_margin, 2),
    }
