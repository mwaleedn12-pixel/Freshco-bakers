"""
Expenses & Net Profit Endpoints.
Manager, Admin, Owner.
"""
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseOut
from app.services import expense_service

router = APIRouter()


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("manager", "admin", "owner")),
) -> list[ExpenseOut]:
    expenses = expense_service.list_expenses(db, branch_id=branch_id)
    return [ExpenseOut.model_validate(e) for e in expenses]


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("manager", "admin", "owner")),
) -> ExpenseOut:
    expense = expense_service.create_expense(
        db,
        actor=actor,
        category=payload.category,
        amount=payload.amount,
        expense_date=payload.expense_date,
        branch_id=payload.branch_id,
        description=payload.description,
    )
    return ExpenseOut.model_validate(expense)


@router.get("/net-profit")
def get_net_profit(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "owner")),
) -> dict[str, Any]:
    return expense_service.get_net_profit_summary(db, branch_id=branch_id)
