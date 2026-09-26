"""
In-app notifications (order updates, low stock alerts, etc.).
"""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class Notification(Base, IDMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(50), default="general")  # order/promo/system/low_stock...
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
