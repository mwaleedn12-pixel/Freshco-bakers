"""
Schemas for Expense Management.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    branch_id: int | None = None
    category: str = Field(min_length=2, max_length=100)
    description: str | None = None
    amount: float = Field(gt=0)
    expense_date: str


class ExpenseOut(BaseModel):
    id: int
    branch_id: int | None = None
    category: str
    description: str | None = None
    amount: float
    expense_date: str
    created_by: int | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
