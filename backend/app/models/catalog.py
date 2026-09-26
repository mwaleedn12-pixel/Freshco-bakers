"""
Catalog: Categories (with subcategories), Products, Product Images.
"""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class Category(Base, IDMixin, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))  # null = top-level category
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")

    parent: Mapped["Category"] = relationship(remote_side="Category.id", back_populates="children")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base, IDMixin, TimestampMixin):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(50), unique=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sale_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    cost_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    track_inventory: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    category: Mapped["Category"] = relationship(back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base, IDMixin):
    __tablename__ = "product_images"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    product: Mapped["Product"] = relationship(back_populates="images")
