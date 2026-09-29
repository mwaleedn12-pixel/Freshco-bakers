from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.branch import BranchCreate, BranchOut, BranchUpdate
from app.services import branch_service

router = APIRouter()
admin_only = require_roles("admin", "owner")


@router.get("", response_model=list[BranchOut])
def list_branches(db: Session = Depends(get_db)):
    """Public: active branches (locations, opening hours) for pickup selection and the contact page."""
    return branch_service.list_branches(db)


@router.get("/admin/list", response_model=list[BranchOut])
def list_all_branches(db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return branch_service.list_branches(db, include_inactive=True)


@router.get("/{branch_id}", response_model=BranchOut)
def get_branch(branch_id: int, db: Session = Depends(get_db)):
    return branch_service.get_branch(db, branch_id)


@router.post("", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(payload: BranchCreate, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return branch_service.create_branch(db, user=user, data=payload.model_dump())


@router.put("/{branch_id}", response_model=BranchOut)
def update_branch(branch_id: int, payload: BranchUpdate, db: Session = Depends(get_db),
                  user: User = Depends(admin_only)):
    """Use status='inactive' to close a branch (branches with order history are never deleted)."""
    return branch_service.update_branch(db, user=user, branch_id=branch_id,
                                        changes=payload.model_dump(exclude_unset=True))
