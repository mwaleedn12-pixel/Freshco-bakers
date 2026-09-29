from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.user import User
from app.services.audit_service import log_action, snapshot
from app.services.errors import ServiceError


def list_branches(db: Session, *, include_inactive: bool = False) -> list[Branch]:
    q = db.query(Branch)
    if not include_inactive:
        q = q.filter(Branch.status == "active")
    return q.order_by(Branch.name).all()


def get_branch(db: Session, branch_id: int, *, include_inactive: bool = False) -> Branch:
    branch = db.get(Branch, branch_id)
    if branch is None or (not include_inactive and branch.status != "active"):
        raise ServiceError("Branch not found", 404)
    return branch


def _check_code(db: Session, code: str | None, exclude_id: int | None = None) -> None:
    if code:
        q = db.query(Branch.id).filter(Branch.code == code)
        if exclude_id:
            q = q.filter(Branch.id != exclude_id)
        if q.first():
            raise ServiceError("A branch with this code already exists", 409)


def create_branch(db: Session, *, user: User, data: dict) -> Branch:
    _check_code(db, data["code"])
    branch = Branch(**data)
    db.add(branch)
    db.flush()
    log_action(db, user_id=user.id, action="branch.create", entity_type="Branch", entity_id=branch.id,
               new_data=snapshot(branch))
    db.commit()
    db.refresh(branch)
    return branch


def update_branch(db: Session, *, user: User, branch_id: int, changes: dict) -> Branch:
    branch = get_branch(db, branch_id, include_inactive=True)
    _check_code(db, changes.get("code"), exclude_id=branch.id)
    old = snapshot(branch)
    for key, value in changes.items():
        setattr(branch, key, value)
    log_action(db, user_id=user.id, action="branch.update", entity_type="Branch", entity_id=branch.id,
               old_data=old, new_data=snapshot(branch))
    db.commit()
    db.refresh(branch)
    return branch
