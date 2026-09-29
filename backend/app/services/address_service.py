from sqlalchemy.orm import Session

from app.models.branch import Address
from app.models.user import User
from app.services.errors import ServiceError


def list_addresses(db: Session, user: User) -> list[Address]:
    return db.query(Address).filter(Address.user_id == user.id).order_by(Address.is_default.desc(), Address.id).all()


def create_address(db: Session, user: User, data: dict) -> Address:
    has_any = db.query(Address.id).filter(Address.user_id == user.id).first() is not None
    make_default = data["is_default"] or not has_any
    if make_default:
        db.query(Address).filter(Address.user_id == user.id).update({"is_default": False})
    data = {**data, "is_default": make_default}
    address = Address(user_id=user.id, **data)
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, user: User, address_id: int) -> None:
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if address is None:
        raise ServiceError("Address not found", 404)
    db.delete(address)
    db.commit()
