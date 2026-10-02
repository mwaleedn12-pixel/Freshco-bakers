"""
Bakery Application Settings Service.
Provides key-value storage for tax, delivery fee, store hours, notification toggles.
"""
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.setting import Setting
from app.models.user import User
from app.services.audit_service import log_action


DEFAULT_SETTINGS = {
    "bakery.name": {"value": "Freshco Bakers", "category": "bakery"},
    "bakery.tagline": {"value": "Freshness Baked Daily in 3D Style", "category": "bakery"},
    "delivery.fee_flat": {"value": 150.0, "category": "delivery"},
    "tax.rate_percent": {"value": 5.0, "category": "tax"},
    "payment.cash_on_delivery": {"value": True, "category": "payment"},
    "payment.online_card": {"value": True, "category": "payment"},
    "notifications.email_enabled": {"value": True, "category": "notification"},
    "notifications.whatsapp_enabled": {"value": True, "category": "notification"},
}


def get_all_settings(db: Session) -> dict[str, Any]:
    rows = list(db.scalars(select(Setting)).all())
    result = {r.key: {"value": r.value, "category": r.category} for r in rows}

    # Fill defaults if missing
    for k, v in DEFAULT_SETTINGS.items():
        if k not in result:
            result[k] = v
    return result


def update_setting(db: Session, key: str, value: Any, category: str = "general", actor: User | None = None) -> Setting:
    setting = db.scalar(select(Setting).where(Setting.key == key))
    if not setting:
        setting = Setting(key=key, value=value, category=category)
        db.add(setting)
    else:
        setting.value = value
        setting.category = category

    if actor:
        log_action(
            db,
            user_id=actor.id if actor else None,
            action="setting.update",
            entity_type="setting",
            entity_id=setting.id if setting.id else 0,
            new_data={"key": key, "value": value},
        )
    db.commit()
    db.refresh(setting)
    return setting


def update_bulk_settings(db: Session, items: list[dict[str, Any]], actor: User | None = None) -> dict[str, Any]:
    for item in items:
        update_setting(
            db,
            key=item["key"],
            value=item.get("value"),
            category=item.get("category", "general"),
            actor=actor,
        )
    return get_all_settings(db)
