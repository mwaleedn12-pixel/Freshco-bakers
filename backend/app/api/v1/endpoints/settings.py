"""
Bakery Application Settings Endpoints.
Public GET (for delivery fee / tax calculation), PUT for Admin & Owner.
"""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.setting import SettingsBulkUpdate
from app.services import setting_service

router = APIRouter()


@router.get("")
def get_settings(db: Session = Depends(get_db)) -> dict[str, Any]:
    return setting_service.get_all_settings(db)


@router.put("")
def update_settings(
    payload: SettingsBulkUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "owner")),
) -> dict[str, Any]:
    items = [item.model_dump() for item in payload.settings]
    return setting_service.update_bulk_settings(db, items, actor=actor)
