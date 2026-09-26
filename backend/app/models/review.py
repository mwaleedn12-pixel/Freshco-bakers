"""
Product reviews with moderation status.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class Review(Base, IDMixin, TimestampMixin):
    __tablename__ = "reviews"

    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/approved/rejected
