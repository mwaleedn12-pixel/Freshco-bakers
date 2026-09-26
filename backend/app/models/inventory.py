"""
Inventory: per-branch stock levels + an immutable transaction log.
Per SRS rule: stock changes are recorded as transactions, never silently overwritten,
and reserved_quantity exists to prevent overselling.
"""
from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class InventoryTransactionType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    ADJUSTMENT = "ADJUSTMENT"
    WASTE = "WASTE"
    RETURN = "RETURN"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


class Inventory(Base, IDMixin, TimestampMixin):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("product_id", "branch_id", name="uq_inventory_product_branch"),)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    minimum_quantity: Mapped[int] = mapped_column(Integer, default=0)  # low-stock threshold


class InventoryTransaction(Base, IDMixin, TimestampMixin):
    __tablename__ = "inventory_transactions"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"))
    type: Mapped[InventoryTransactionType] = mapped_column(Enum(InventoryTransactionType), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # signed: +in, -out
    reference_type: Mapped[str | None] = mapped_column(String(50))  # e.g. "order", "return", "manual"
    reference_id: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
