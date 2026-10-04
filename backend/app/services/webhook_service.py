"""
n8n Webhook & Automation Dispatcher Service.
Dispatches real-time domain events to n8n workflows for:
- WhatsApp / SMS / Email customer notifications
- Kitchen / Bakery owner instant alerts
- Real-time inventory sync & low-stock triggers
- Custom cake request quote pipelines
- Daily automated financial reporting
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger("freshco.webhooks")


def _compute_signature(payload_bytes: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for payload verification in n8n."""
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def _send_http_post(url: str, payload_dict: dict[str, Any], secret: str, timeout: float = 3.0) -> bool:
    """Synchronous HTTP worker executed inside daemon thread / background task."""
    try:
        data = json.dumps(payload_dict, default=str).encode("utf-8")
        signature = _compute_signature(data, secret)

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "FreshcoBakers-Webhook/1.0",
                "X-Freshco-Signature": f"sha256={signature}",
                "X-Freshco-Event": payload_dict.get("event", "unknown"),
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            logger.info("Dispatched event '%s' to n8n [%s] -> Status %s",
                        payload_dict.get("event"), url, status_code)
            return 200 <= status_code < 300
    except urllib.error.HTTPError as e:
        logger.warning("n8n Webhook HTTP error [%s]: %s (%s)", url, e.code, e.reason)
        return False
    except Exception as e:
        logger.debug("n8n Webhook delivery skipped or connection refused [%s]: %s", url, e)
        return False


def dispatch_event(event_name: str, payload: dict[str, Any], async_mode: bool = True) -> bool:
    """
    Dispatches a structured event payload to the configured n8n webhook URL.
    By default executes asynchronously in a background thread to prevent blocking client responses.
    """
    if not settings.N8N_ENABLED or not settings.N8N_WEBHOOK_URL:
        return False

    envelope = {
        "event": event_name,
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "data": payload,
    }

    if async_mode:
        thread = threading.Thread(
            target=_send_http_post,
            args=(settings.N8N_WEBHOOK_URL, envelope, settings.N8N_WEBHOOK_SECRET, settings.N8N_TIMEOUT_SECONDS),
            daemon=True,
            name=f"n8n-webhook-{event_name}",
        )
        thread.start()
        return True
    else:
        return _send_http_post(
            settings.N8N_WEBHOOK_URL, envelope, settings.N8N_WEBHOOK_SECRET, settings.N8N_TIMEOUT_SECONDS
        )


# ─── Specialized Event Dispatch Helpers ─────────────────────────────────────

def dispatch_order_created(
    order_id: int,
    order_number: str,
    customer_name: str,
    customer_phone: str,
    customer_email: str | None,
    order_source: str,
    order_type: str,
    items: list[dict[str, Any]],
    subtotal: float,
    discount: float,
    tax: float,
    delivery_fee: float,
    total_amount: float,
    payment_method: str,
    branch_name: str,
    delivery_address: str | None = None,
    special_instructions: str | None = None,
) -> None:
    """Dispatched immediately when an order is created on Website / POS / WhatsApp."""
    items_summary = ", ".join(f"{item.get('name', 'Item')} x{item.get('quantity', 1)}" for item in items)
    
    payload = {
        "order_id": order_id,
        "order_number": order_number,
        "customer": {
            "name": customer_name,
            "phone": customer_phone,
            "email": customer_email,
        },
        "order_source": order_source,
        "order_type": order_type,
        "branch_name": branch_name,
        "delivery_address": delivery_address or "Bakery Counter Pickup",
        "special_instructions": special_instructions,
        "items": items,
        "items_summary": items_summary,
        "financials": {
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "delivery_fee": delivery_fee,
            "total_amount": total_amount,
            "payment_method": payment_method,
        },
        "tracking_url": f"http://localhost:3000/orders/{order_id}",
    }
    dispatch_event("order.created", payload)


def dispatch_order_status_updated(
    order_id: int,
    order_number: str,
    old_status: str,
    new_status: str,
    customer_name: str | None,
    customer_phone: str | None,
    customer_email: str | None,
    note: str | None = None,
) -> None:
    """Dispatched whenever kitchen or staff updates the order progress status."""
    payload = {
        "order_id": order_id,
        "order_number": order_number,
        "old_status": old_status,
        "new_status": new_status,
        "customer": {
            "name": customer_name or "Valued Customer",
            "phone": customer_phone,
            "email": customer_email,
        },
        "note": note,
        "tracking_url": f"http://localhost:3000/orders/{order_id}",
    }
    dispatch_event("order.status_updated", payload)


def dispatch_low_stock_alert(
    product_id: int,
    product_name: str,
    sku: str,
    branch_id: int,
    branch_name: str,
    current_quantity: int,
    minimum_quantity: int,
) -> None:
    """Dispatched when inventory drops below safety threshold."""
    payload = {
        "product_id": product_id,
        "product_name": product_name,
        "sku": sku,
        "branch_id": branch_id,
        "branch_name": branch_name,
        "current_quantity": current_quantity,
        "minimum_quantity": minimum_quantity,
        "deficit": max(0, minimum_quantity - current_quantity),
    }
    dispatch_event("inventory.low_stock", payload)


def dispatch_custom_cake_event(
    cake_id: int,
    customer_name: str,
    customer_phone: str,
    flavour: str | None,
    cake_type: str | None,
    requested_date: str | None,
    quote_amount: float | None,
    status: str,
    event_type: str = "requested",
) -> None:
    """Dispatched for custom cake requests or quote updates."""
    payload = {
        "cake_id": cake_id,
        "event_type": event_type,
        "customer": {
            "name": customer_name,
            "phone": customer_phone,
        },
        "cake_details": {
            "flavour": flavour,
            "type": cake_type,
            "requested_date": requested_date,
            "quote_amount": quote_amount,
            "status": status,
        },
    }
    dispatch_event(f"custom_cake.{event_type}", payload)
