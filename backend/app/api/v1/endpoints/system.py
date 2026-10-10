"""
System management & operational telemetry endpoints for Freshco Bakers.
Provides runtime metrics, live database stats, and demo-seeding controls.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.branch import Branch
from app.models.catalog import Category, Product
from app.models.order import Order
from app.models.review import Review
from app.models.user import User
from app.scripts.seed_demo_data import seed_data

router = APIRouter(prefix="/system", tags=["system diagnostics"])

START_TIME = time.time()


@router.get("/info", summary="System Information & Configuration")
def get_system_info() -> dict[str, Any]:
    uptime_sec = int(time.time() - START_TIME)
    return {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "uptime_seconds": uptime_sec,
        "uptime_human": f"{uptime_sec // 3600}h {(uptime_sec % 3600) // 60}m {uptime_sec % 60}s",
        "python_version": sys.version.split()[0],
        "api_v1_prefix": settings.API_V1_PREFIX,
        "rate_limiting": {
            "enabled": settings.RATE_LIMIT_ENABLED,
            "per_minute": settings.RATE_LIMIT_PER_MINUTE,
        },
        "n8n_automation": {
            "enabled": settings.N8N_ENABLED,
            "webhook_configured": bool(settings.N8N_WEBHOOK_URL),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stats", summary="Live Database Entity Counts")
def get_system_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        product_count = db.query(func.count(Product.id)).scalar() or 0
        category_count = db.query(func.count(Category.id)).scalar() or 0
        branch_count = db.query(func.count(Branch.id)).scalar() or 0
        order_count = db.query(func.count(Order.id)).scalar() or 0
        user_count = db.query(func.count(User.id)).scalar() or 0
        review_count = db.query(func.count(Review.id)).scalar() or 0

        return {
            "status": "connected",
            "database": "PostgreSQL (Connected)",
            "products": product_count,
            "categories": category_count,
            "branches": branch_count,
            "orders": order_count,
            "users": user_count,
            "reviews": review_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        return {
            "status": "partial",
            "database": f"DB Warning: {str(exc)[:60]}",
            "products": 0,
            "categories": 0,
            "branches": 0,
            "orders": 0,
            "users": 0,
            "reviews": 0,
        }


@router.post("/seed", summary="Populate Demo Bakery Data")
def trigger_seed_demo_data() -> dict[str, Any]:
    try:
        seed_data()
        return {
            "status": "success",
            "message": "Freshco Bakers demo data populated successfully!",
            "details": "Users, Branches, Categories, Products, Inventory, Orders, POS sales & Reviews ready.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to seed demo data: {exc}")
