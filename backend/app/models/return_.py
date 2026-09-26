"""
Returns — creates a RETURN inventory transaction per SRS order/inventory rules.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class Return(Base, IDMixin, TimestampMixin):
    __tablename__ = "returns"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    order_item_id: Mapped[int | None] = mapped_column(ForeignKey("order_items.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/approved/rejected/completed
    refund_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
