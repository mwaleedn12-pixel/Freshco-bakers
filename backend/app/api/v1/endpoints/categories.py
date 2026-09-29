from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.catalog import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import catalog_service
from app.services.errors import ServiceError

router = APIRouter()
admin_only = require_roles("admin", "owner")


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    """Public: active categories (top-level and sub-categories, ordered)."""
    return catalog_service.list_categories(db)


@router.get("/admin/list", response_model=list[CategoryOut])
def list_all_categories(db: Session = Depends(get_db), user: User = Depends(admin_only)):
    """Admin: includes inactive categories."""
    return catalog_service.list_categories(db, include_inactive=True)


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = catalog_service.get_category(db, category_id)
    if cat.status != "active":
        raise ServiceError("Category not found", 404)
    return cat


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return catalog_service.create_category(db, user=user, data=payload.model_dump())


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db),
                    user: User = Depends(admin_only)):
    return catalog_service.update_category(db, user=user, category_id=category_id,
                                           changes=payload.model_dump(exclude_unset=True))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    catalog_service.delete_category(db, user=user, category_id=category_id)
