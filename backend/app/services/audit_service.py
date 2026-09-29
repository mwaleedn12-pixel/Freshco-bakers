"""
Audit logging helper (SRS: keep audit logs for sensitive administrative changes).
Callers add the log inside their own transaction and commit once.
"""
from __future__ import annotations

import enum
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def snapshot(obj: Any) -> dict:
    """JSON-safe copy of a model row's columns."""
    data: dict[str, Any] = {}
    for col in obj.__table__.columns:
        value = getattr(obj, col.key)
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (datetime, date, time)):
            value = value.isoformat()
        elif isinstance(value, enum.Enum):
            value = value.value
        data[col.key] = value
    return data


def log_action(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    old_data: dict | None = None,
    new_data: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
        )
    )
