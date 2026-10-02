"""
Audit Logs Endpoint (Owner/Admin Only).
"""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()


@router.get("")
def list_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "owner")),
) -> list[dict[str, Any]]:
    logs = list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all())
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "old_data": l.old_data,
            "new_data": l.new_data,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
