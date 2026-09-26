"""
Branch expenses — feeds Phase 3 profit analytics (revenue - cost_price - expenses).
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class Expense(Base, IDMixin, TimestampMixin):
    __tablename__ = "expenses"

    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # rent, utilities, ingredients, salaries...
    description: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    expense_date: Mapped[str] = mapped_column(String(20), nullable=False)  # ISO date string
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
