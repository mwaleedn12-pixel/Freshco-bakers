"""
Audit logs — tracks sensitive administrative changes (SRS security requirement).
old_data/new_data store JSON snapshots for before/after comparison.
"""
from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IDMixin, TimestampMixin


class AuditLog(Base, IDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "product.update", "order.cancel"
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Product", "Order"
    entity_id: Mapped[int | None] = mapped_column(Integer)
    old_data: Mapped[dict | None] = mapped_column(JSON)
    new_data: Mapped[dict | None] = mapped_column(JSON)
