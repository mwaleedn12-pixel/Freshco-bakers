"""
Customer wishlists.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class Wishlist(Base, IDMixin, TimestampMixin):
    __tablename__ = "wishlists"

    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    items: Mapped[list["WishlistItem"]] = relationship(back_populates="wishlist", cascade="all, delete-orphan")


class WishlistItem(Base, IDMixin):
    __tablename__ = "wishlist_items"

    wishlist_id: Mapped[int] = mapped_column(ForeignKey("wishlists.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))

    wishlist: Mapped["Wishlist"] = relationship(back_populates="items")
