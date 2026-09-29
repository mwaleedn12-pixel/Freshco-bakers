from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.custom_cake import (
    CakeStatusChange, CustomCakeAdminOut, CustomCakeAdminPage, CustomCakeCreate, CustomCakeOut, CustomCakePage,
    QuoteRequest,
)
from app.services import custom_cake_service as svc

router = APIRouter()
staff = require_roles("manager", "admin", "owner")


def _admin_out(req, customer) -> CustomCakeAdminOut:
    return CustomCakeAdminOut(**CustomCakeOut.model_validate(req).model_dump(), customer_id=req.customer_id,
                              customer_name=customer.name if customer else None,
                              customer_phone=customer.phone if customer else None, notes=req.notes)


def _admin_one(db: Session, req) -> CustomCakeAdminOut:
    return _admin_out(req, db.get(User, req.customer_id))


# ------------------------------------------------------------------ customer
@router.post("", response_model=CustomCakeOut, status_code=status.HTTP_201_CREATED)
def create_request(payload: CustomCakeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.create_request(db, user, payload.model_dump())


@router.get("", response_model=CustomCakePage)
def my_requests(page: int = Query(default=1, ge=1), limit: int = Query(default=20, ge=1, le=100),
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items, total = svc.list_mine(db, user, page=page, limit=limit)
    return CustomCakePage(items=items, total=total, page=page, limit=limit)


# --------------------------------------------------------------------- staff
@router.get("/admin/list", response_model=CustomCakeAdminPage)
def admin_list(status: str | None = Query(default=None, pattern="^(pending|quoted|accepted|in_progress|done|rejected|cancelled)$"),
               page: int = Query(default=1, ge=1), limit: int = Query(default=20, ge=1, le=100),
               db: Session = Depends(get_db), user: User = Depends(staff)):
    rows, customers, total = svc.list_admin(db, status=status, page=page, limit=limit)
    return CustomCakeAdminPage(items=[_admin_out(r, customers.get(r.customer_id)) for r in rows],
                               total=total, page=page, limit=limit)


@router.patch("/{request_id}/quote", response_model=CustomCakeAdminOut)
def quote(request_id: int, payload: QuoteRequest, db: Session = Depends(get_db), user: User = Depends(staff)):
    req = svc.quote(db, user=user, request_id=request_id, amount=payload.quote_amount, notes=payload.notes)
    return _admin_one(db, req)


@router.patch("/{request_id}/status", response_model=CustomCakeAdminOut)
def change_status(request_id: int, payload: CakeStatusChange, db: Session = Depends(get_db),
                  user: User = Depends(staff)):
    req = svc.admin_change_status(db, user=user, request_id=request_id, new_status=payload.status,
                                  notes=payload.notes)
    return _admin_one(db, req)


# ------------------------------------------------------- customer (by id)
@router.get("/{request_id}", response_model=CustomCakeOut)
def get_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.get_for_customer(db, user, request_id)


@router.patch("/{request_id}/accept", response_model=CustomCakeOut)
def accept_quote(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.customer_accept(db, user, request_id)


@router.patch("/{request_id}/cancel", response_model=CustomCakeOut)
def cancel_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.customer_cancel(db, user, request_id)
