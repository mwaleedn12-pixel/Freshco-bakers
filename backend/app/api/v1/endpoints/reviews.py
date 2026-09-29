from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import ModerateRequest, ProductReviews, ReviewCreate, ReviewOut, ReviewPage
from app.services import review_service

router = APIRouter()
staff = require_roles("manager", "admin", "owner")


@router.get("/product/{product_id}", response_model=ProductReviews)
def product_reviews(product_id: int, page: int = Query(default=1, ge=1), limit: int = Query(default=10, ge=1, le=50),
                    db: Session = Depends(get_db)):
    """Public: approved reviews + average rating + star distribution for a product."""
    return review_service.product_reviews(db, product_id, page=page, limit=limit)


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return review_service.create_review(db, user, product_id=payload.product_id, rating=payload.rating,
                                        comment=payload.comment)


@router.get("/mine", response_model=ReviewPage)
def my_reviews(page: int = Query(default=1, ge=1), limit: int = Query(default=20, ge=1, le=100),
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items, total = review_service.my_reviews(db, user, page=page, limit=limit)
    return ReviewPage(items=items, total=total, page=page, limit=limit)


@router.get("/admin/list", response_model=ReviewPage)
def admin_list(status: str | None = Query(default=None, pattern="^(pending|approved|rejected)$"),
               product_id: int | None = None, page: int = Query(default=1, ge=1),
               limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db),
               user: User = Depends(staff)):
    items, total = review_service.admin_list(db, status=status, product_id=product_id, page=page, limit=limit)
    return ReviewPage(items=items, total=total, page=page, limit=limit)


@router.patch("/{review_id}/moderate", response_model=ReviewOut)
def moderate(review_id: int, payload: ModerateRequest, db: Session = Depends(get_db), user: User = Depends(staff)):
    return review_service.moderate(db, user=user, review_id=review_id, new_status=payload.status)
