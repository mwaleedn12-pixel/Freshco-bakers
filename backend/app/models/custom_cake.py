"""
Custom cake requests — customer submits, admin quotes and tracks status (section 6).
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class CustomCakeRequest(Base, IDMixin, TimestampMixin):
    __tablename__ = "custom_cake_requests"

    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str | None] = mapped_column(String(100))
    flavour: Mapped[str | None] = mapped_column(String(100))
    size: Mapped[str | None] = mapped_column(String(50))
    cream: Mapped[str | None] = mapped_column(String(100))
    theme: Mapped[str | None] = mapped_column(String(150))
    message: Mapped[str | None] = mapped_column(Text)  # message to write on the cake
    reference_image: Mapped[str | None] = mapped_column(String(500))
    requested_date: Mapped[str | None] = mapped_column(String(50))  # needed-by date (ISO string)
    quote_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending/quoted/accepted/in_progress/done/cancelled
    notes: Mapped[str | None] = mapped_column(Text)  # internal admin notes

    customer: Mapped["User"] = relationship()
