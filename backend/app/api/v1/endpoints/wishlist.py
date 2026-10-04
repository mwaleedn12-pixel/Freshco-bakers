from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.wishlist import WishlistItemAdd, WishlistItemOut
from app.services import wishlist_service

router = APIRouter()


@router.get("", response_model=list[WishlistItemOut])
def get_wishlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return wishlist_service.list_wishlist(db, user)


@router.post("/items", response_model=list[WishlistItemOut])
def add_item(payload: WishlistItemAdd, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return wishlist_service.add_item(db, user, payload.product_id)


@router.delete("/items/{item_id}", response_model=list[WishlistItemOut])
def remove_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return wishlist_service.remove_item(db, user, item_id)
