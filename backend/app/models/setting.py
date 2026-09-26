"""
Key-value application settings (bakery info, delivery, tax, payment, notifications — section 6).
"""
from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class Setting(Base, IDMixin, TimestampMixin):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)  # e.g. "delivery.fee_flat"
    value: Mapped[dict | None] = mapped_column(JSON)
    category: Mapped[str] = mapped_column(String(50), default="general")  # bakery/delivery/tax/payment/notification
