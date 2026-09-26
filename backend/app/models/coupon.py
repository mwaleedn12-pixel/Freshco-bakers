"""
Offers/Coupons — percentage or fixed discounts, with limits and expiry (section 6).
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class CouponType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"


class Coupon(Base, IDMixin, TimestampMixin):
    __tablename__ = "coupons"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type: Mapped[CouponType] = mapped_column(Enum(CouponType), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    min_order_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    usage_limit: Mapped[int | None] = mapped_column(Integer)  # total times this coupon can be used
    per_customer_limit: Mapped[int | None] = mapped_column(Integer)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")

    usages: Mapped[list["CouponUsage"]] = relationship(back_populates="coupon", cascade="all, delete-orphan")


class CouponUsage(Base, IDMixin):
    __tablename__ = "coupon_usages"

    coupon_id: Mapped[int] = mapped_column(ForeignKey("coupons.id", ondelete="CASCADE"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    coupon: Mapped["Coupon"] = relationship(back_populates="usages")
