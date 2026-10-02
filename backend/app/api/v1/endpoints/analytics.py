"""
Analytics & Reports Endpoints (Manager, Admin & Owner).
"""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.services import analytics_service

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("manager", "admin", "owner")),
) -> dict[str, Any]:
    return analytics_service.get_dashboard_summary(db)


@router.get("/channels")
def get_channel_split(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("manager", "admin", "owner")),
) -> dict[str, Any]:
    return analytics_service.get_sales_channel_split(db)


@router.get("/profit")
def get_profit_report(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "owner")),
) -> dict[str, Any]:
    return analytics_service.get_gross_profit_report(db)
