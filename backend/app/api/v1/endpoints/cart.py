from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartOut
from app.services import cart_service

router = APIRouter()


@router.get("", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return cart_service.build_cart_out(db, cart_service.get_or_create_cart(db, user))


@router.post("/items", response_model=CartOut)
def add_item(payload: CartItemAdd, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = cart_service.add_item(db, user, payload.product_id, payload.quantity)
    return cart_service.build_cart_out(db, cart)


@router.patch("/items/{item_id}", response_model=CartOut)
def update_item(item_id: int, payload: CartItemUpdate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    cart = cart_service.update_item(db, user, item_id, payload.quantity)
    return cart_service.build_cart_out(db, cart)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return cart_service.build_cart_out(db, cart_service.remove_item(db, user, item_id))


@router.delete("", response_model=CartOut)
def clear_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return cart_service.build_cart_out(db, cart_service.clear_cart(db, user))
