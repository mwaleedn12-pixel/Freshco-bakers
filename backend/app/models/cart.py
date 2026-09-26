"""
Shopping cart (website customer flow, before checkout creates an Order).
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class Cart(Base, IDMixin, TimestampMixin):
    __tablename__ = "carts"

    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base, IDMixin):
    __tablename__ = "cart_items"

    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # snapshot at add-to-cart time

    cart: Mapped["Cart"] = relationship(back_populates="items")
