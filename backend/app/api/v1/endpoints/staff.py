"""
Staff Management Endpoints.
Accessible by Admin & Owner.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.staff import StaffCreate, StaffOut, StaffUpdate
from app.services import staff_service

router = APIRouter()


@router.get("", response_model=list[StaffOut])
def list_staff(
    role: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "owner")),
) -> list[StaffOut]:
    staff_members = staff_service.list_staff(db, role=role)
    return [
        StaffOut(
            id=s.id,
            name=s.name,
            email=s.email,
            phone=s.phone,
            role=s.role.name if s.role else "staff",
            status=s.status,
        )
        for s in staff_members
    ]


@router.post("", response_model=StaffOut, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "owner")),
) -> StaffOut:
    try:
        staff_user = staff_service.create_staff(
            db,
            actor=actor,
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role_name=payload.role,
            phone=payload.phone,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return StaffOut(
        id=staff_user.id,
        name=staff_user.name,
        email=staff_user.email,
        phone=staff_user.phone,
        role=staff_user.role.name if staff_user.role else payload.role,
        status=staff_user.status,
    )


@router.put("/{staff_id}", response_model=StaffOut)
def update_staff(
    staff_id: int,
    payload: StaffUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "owner")),
) -> StaffOut:
    try:
        updated = staff_service.update_staff(
            db,
            actor=actor,
            staff_id=staff_id,
            name=payload.name,
            phone=payload.phone,
            role_name=payload.role,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return StaffOut(
        id=updated.id,
        name=updated.name,
        email=updated.email,
        phone=updated.phone,
        role=updated.role.name if updated.role else "staff",
        status=updated.status,
    )
