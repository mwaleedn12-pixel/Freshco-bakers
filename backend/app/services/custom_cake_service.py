"""
Custom cake requests.
  pending -> quoted (admin) -> accepted (customer) -> in_progress -> done
  cancelled: customer (pending/quoted/accepted) or admin; rejected: admin (pending/quoted)
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.custom_cake import CustomCakeRequest
from app.models.user import User
from app.services.audit_service import log_action, snapshot
from app.services.errors import ServiceError
from app.services.notification_service import notify, notify_staff
from app.services import webhook_service

ADMIN_TRANSITIONS = {
    "pending": {"quoted", "rejected", "cancelled"},
    "quoted": {"quoted", "rejected", "cancelled"},
    "accepted": {"in_progress", "cancelled"},
    "in_progress": {"done", "cancelled"},
}
CUSTOMER_CANCELLABLE = {"pending", "quoted", "accepted"}
STATUS_TEXT = {"in_progress": "is now being made", "done": "is ready", "rejected": "could not be accepted",
               "cancelled": "was cancelled"}


def _get(db: Session, request_id: int) -> CustomCakeRequest:
    req = db.get(CustomCakeRequest, request_id)
    if req is None:
        raise ServiceError("Custom cake request not found", 404)
    return req


def get_for_customer(db: Session, user: User, request_id: int) -> CustomCakeRequest:
    req = _get(db, request_id)
    role = user.role.name if user.role else None
    if req.customer_id != user.id and role not in ("manager", "admin", "owner"):
        raise ServiceError("Custom cake request not found", 404)
    return req


def create_request(db: Session, user: User, data: dict) -> CustomCakeRequest:
    if data["requested_date"] <= date.today():
        raise ServiceError("Requested date must be in the future", 400)
    data = {**data, "requested_date": data["requested_date"].isoformat()}
    req = CustomCakeRequest(customer_id=user.id, status="pending", **data)
    db.add(req)
    db.flush()
    notify_staff(db, "New custom cake request", f"{user.name}: {req.flavour}, {req.size}, needed by {req.requested_date}",
                 "custom_cake")
    notify(db, user.id, "Custom cake request received",
           "We will review your request and send you a quotation soon.", "custom_cake")
    db.commit()
    db.refresh(req)

    # Trigger n8n Automation Webhook
    try:
        webhook_service.dispatch_custom_cake_event(
            cake_id=req.id,
            customer_name=user.name or "Customer",
            customer_phone=user.phone or "",
            flavour=req.flavour,
            cake_type=req.size,
            requested_date=str(req.requested_date),
            quote_amount=float(req.quote_amount) if req.quote_amount else None,
            status=req.status,
            event_type="requested",
        )
    except Exception:
        pass

    return req


def list_mine(db: Session, user: User, *, page: int, limit: int):
    q = db.query(CustomCakeRequest).filter(CustomCakeRequest.customer_id == user.id)
    total = q.count()
    return q.order_by(CustomCakeRequest.id.desc()).offset((page - 1) * limit).limit(limit).all(), total


def list_admin(db: Session, *, status: str | None, page: int, limit: int):
    q = db.query(CustomCakeRequest)
    if status:
        q = q.filter(CustomCakeRequest.status == status)
    total = q.count()
    rows = q.order_by(CustomCakeRequest.id.desc()).offset((page - 1) * limit).limit(limit).all()
    ids = {r.customer_id for r in rows}
    customers = {u.id: u for u in db.query(User).filter(User.id.in_(ids))} if ids else {}
    return rows, customers, total


def quote(db: Session, *, user: User, request_id: int, amount: float, notes: str | None) -> CustomCakeRequest:
    req = _get(db, request_id)
    if "quoted" not in ADMIN_TRANSITIONS.get(req.status, set()):
        raise ServiceError(f"Cannot quote a request that is {req.status}", 400)
    old = snapshot(req)
    req.quote_amount = amount
    req.status = "quoted"
    if notes is not None:
        req.notes = notes
    notify(db, req.customer_id, "Your custom cake quotation",
           f"Quotation: {amount:,.2f}. Please open your request to accept it.", "custom_cake")
    log_action(db, user_id=user.id, action="custom_cake.quote", entity_type="CustomCakeRequest",
               entity_id=req.id, old_data=old, new_data=snapshot(req))
    db.commit()
    db.refresh(req)

    # Trigger n8n webhook
    try:
        customer = db.get(User, req.customer_id)
        webhook_service.dispatch_custom_cake_event(
            cake_id=req.id,
            customer_name=customer.name if customer else "Customer",
            customer_phone=customer.phone if customer else "",
            flavour=req.flavour,
            cake_type=req.size,
            requested_date=str(req.requested_date),
            quote_amount=float(req.quote_amount) if req.quote_amount else None,
            status="quoted",
            event_type="quoted",
        )
    except Exception:
        pass

    return req


def admin_change_status(db: Session, *, user: User, request_id: int, new_status: str,
                        notes: str | None) -> CustomCakeRequest:
    req = _get(db, request_id)
    if new_status not in ADMIN_TRANSITIONS.get(req.status, set()):
        raise ServiceError(f"Cannot change request from {req.status} to {new_status}", 400)
    old = snapshot(req)
    req.status = new_status
    if notes is not None:
        req.notes = notes
    notify(db, req.customer_id, "Custom cake update", f"Your custom cake {STATUS_TEXT[new_status]}.", "custom_cake")
    log_action(db, user_id=user.id, action="custom_cake.status", entity_type="CustomCakeRequest",
               entity_id=req.id, old_data=old, new_data=snapshot(req))
    db.commit()
    db.refresh(req)

    # Trigger n8n webhook
    try:
        customer = db.get(User, req.customer_id)
        webhook_service.dispatch_custom_cake_event(
            cake_id=req.id,
            customer_name=customer.name if customer else "Customer",
            customer_phone=customer.phone if customer else "",
            flavour=req.flavour,
            cake_type=req.size,
            requested_date=str(req.requested_date),
            quote_amount=float(req.quote_amount) if req.quote_amount else None,
            status=new_status,
            event_type="status_changed",
        )
    except Exception:
        pass

    return req


def customer_accept(db: Session, user: User, request_id: int) -> CustomCakeRequest:
    req = _get(db, request_id)
    if req.customer_id != user.id:
        raise ServiceError("Custom cake request not found", 404)
    if req.status != "quoted":
        raise ServiceError("Only a quoted request can be accepted", 400)
    req.status = "accepted"
    notify_staff(db, "Custom cake quotation accepted", f"{user.name} accepted request #{req.id}", "custom_cake")
    db.commit()
    db.refresh(req)
    return req


def customer_cancel(db: Session, user: User, request_id: int) -> CustomCakeRequest:
    req = _get(db, request_id)
    if req.customer_id != user.id:
        raise ServiceError("Custom cake request not found", 404)
    if req.status not in CUSTOMER_CANCELLABLE:
        raise ServiceError("This request can no longer be cancelled", 400)
    req.status = "cancelled"
    notify_staff(db, "Custom cake request cancelled", f"{user.name} cancelled request #{req.id}", "custom_cake")
    db.commit()
    db.refresh(req)
    return req
