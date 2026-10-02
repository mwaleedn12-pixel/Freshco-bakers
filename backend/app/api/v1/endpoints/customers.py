"""
Customer Analytics & Management Endpoints.
Accessible by Manager, Admin & Owner.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.customer import CustomerDetailOut, CustomerOut
from app.services import customer_service

router = APIRouter()


@router.get("", response_model=list[CustomerOut])
def list_customers(
    search: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("manager", "admin", "owner")),
) -> list[CustomerOut]:
    return customer_service.list_customers(db, search=search)


@router.get("/{customer_id}", response_model=CustomerDetailOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("manager", "admin", "owner")),
) -> CustomerDetailOut:
    detail = customer_service.get_customer_detail(db, customer_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return CustomerDetailOut(**detail)
