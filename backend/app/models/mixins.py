"""
Shared mixins used across models: primary key + created/updated timestamps.
"""
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class IDMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
