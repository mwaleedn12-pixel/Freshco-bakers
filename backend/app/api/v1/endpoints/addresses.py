from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.address import AddressCreate, AddressOut
from app.services import address_service

router = APIRouter()


@router.get("", response_model=list[AddressOut])
def list_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return address_service.list_addresses(db, user)


@router.post("", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return address_service.create_address(db, user, payload.model_dump())


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    address_service.delete_address(db, user, address_id)
