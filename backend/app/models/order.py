"""
Orders — the shared model for BOTH website checkout and POS sales (SRS section 7/10).
order_source distinguishes WEBSITE / POS / PHONE / WHATSAPP.
order_status and payment_status are kept separate, as required by the SRS.
"""
from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class OrderSource(str, enum.Enum):
    WEBSITE = "WEBSITE"
    POS = "POS"
    PHONE = "PHONE"
    WHATSAPP = "WHATSAPP"


class OrderType(str, enum.Enum):
    DELIVERY = "DELIVERY"
    PICKUP = "PICKUP"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    PICKED_UP = "PICKED_UP"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    CARD = "CARD"
    ONLINE = "ONLINE"
    WALLET = "WALLET"


class Order(Base, IDMixin, TimestampMixin):
    __tablename__ = "orders"

    order_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # nullable: walk-in POS sale
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))

    order_source: Mapped[OrderSource] = mapped_column(Enum(OrderSource), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), default=OrderType.PICKUP)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)

    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    discount_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tax_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    delivery_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    address_id: Mapped[int | None] = mapped_column(ForeignKey("addresses.id"))
    scheduled_at: Mapped[str | None] = mapped_column(String(50))  # ISO datetime string for scheduled pickup/delivery
    notes: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base, IDMixin):
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))

    # Snapshots — historical order_items must preserve name/price even if the product changes later.
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")


class Payment(Base, IDMixin, TimestampMixin):
    __tablename__ = "payments"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    transaction_reference: Mapped[str | None] = mapped_column(String(150))
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    paid_at: Mapped[str | None] = mapped_column(String(50))

    order: Mapped["Order"] = relationship(back_populates="payments")


class OrderStatusHistory(Base, IDMixin, TimestampMixin):
    __tablename__ = "order_status_history"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="status_history")
