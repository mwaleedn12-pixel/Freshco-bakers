"""
Branches (multi-branch support, section 10/17) and customer/delivery Addresses.
"""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class Branch(Base, IDMixin, TimestampMixin):
    __tablename__ = "branches"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(30))
    opening_time: Mapped[str | None] = mapped_column(Time)
    closing_time: Mapped[str | None] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(20), default="active")


class Address(Base, IDMixin, TimestampMixin):
    __tablename__ = "addresses"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    label: Mapped[str | None] = mapped_column(String(50))  # Home, Office, etc.
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="addresses")
