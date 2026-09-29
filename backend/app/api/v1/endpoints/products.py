from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.catalog import (
    ProductAdminOut,
    ProductAdminPage,
    ProductCreate,
    ProductImageCreate,
    ProductOut,
    ProductPage,
    ProductUpdate,
)
from app.services import catalog_service

router = APIRouter()
admin_only = require_roles("admin", "owner")


@router.get("", response_model=ProductPage)
def list_products(
    category_id: int | None = None,
    search: str | None = Query(default=None, max_length=100),
    featured: bool | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Public catalog: only active products, no cost price."""
    items, total = catalog_service.list_products(
        db, category_id=category_id, search=search, featured=featured, page=page, limit=limit
    )
    return ProductPage(items=items, total=total, page=page, limit=limit)


@router.get("/admin/list", response_model=ProductAdminPage)
def list_products_admin(
    category_id: int | None = None,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    """Admin: all products including inactive/archived, with cost price."""
    items, total = catalog_service.list_products(
        db, category_id=category_id, search=search, include_inactive=True, page=page, limit=limit
    )
    return ProductAdminPage(items=items, total=total, page=page, limit=limit)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return catalog_service.get_product(db, product_id)


@router.post("", response_model=ProductAdminOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return catalog_service.create_product(db, user=user, data=payload.model_dump())


@router.put("/{product_id}", response_model=ProductAdminOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db),
                   user: User = Depends(admin_only)):
    return catalog_service.update_product(db, user=user, product_id=product_id,
                                          changes=payload.model_dump(exclude_unset=True))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    catalog_service.archive_product(db, user=user, product_id=product_id)


@router.post("/{product_id}/images", response_model=ProductAdminOut, status_code=status.HTTP_201_CREATED)
def add_image(product_id: int, payload: ProductImageCreate, db: Session = Depends(get_db),
              user: User = Depends(admin_only)):
    return catalog_service.add_image(db, user=user, product_id=product_id, data=payload.model_dump())


@router.delete("/{product_id}/images/{image_id}", response_model=ProductAdminOut)
def remove_image(product_id: int, image_id: int, db: Session = Depends(get_db),
                 user: User = Depends(admin_only)):
    return catalog_service.remove_image(db, user=user, product_id=product_id, image_id=image_id)
