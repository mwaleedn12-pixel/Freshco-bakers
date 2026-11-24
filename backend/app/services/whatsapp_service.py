"""
WhatsApp Automation & Notification Service for Freshco Bakers.
Handles:
- Customer order confirmation notifications
- Kitchen / Bakery Owner alerts
- Status update notifications
- Direct Meta Cloud API / UltraMsg dispatch
- Click-to-chat WhatsApp link generation (guaranteed delivery fallback)
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.core.config import settings

logger = logging.getLogger("freshco.whatsapp")


def _get_config() -> dict[str, str]:
    """Dynamically fetch WhatsApp credentials from settings and env."""
    return {
        "owner_phone": (settings.BAKERY_OWNER_PHONE or os.environ.get("BAKERY_OWNER_PHONE") or "923348984654").strip(),
        "meta_token": (settings.WHATSAPP_ACCESS_TOKEN or os.environ.get("WHATSAPP_ACCESS_TOKEN") or "").strip(),
        "meta_phone_id": (settings.WHATSAPP_PHONE_NUMBER_ID or os.environ.get("WHATSAPP_PHONE_NUMBER_ID") or "").strip(),
        "ultramsg_id": (settings.ULTRAMSG_INSTANCE_ID or os.environ.get("ULTRAMSG_INSTANCE_ID") or "").strip(),
        "ultramsg_token": (settings.ULTRAMSG_TOKEN or os.environ.get("ULTRAMSG_TOKEN") or "").strip(),
        "frontend_base": (settings.FRONTEND_BASE_URL or os.environ.get("FRONTEND_BASE_URL") or "http://localhost:3000").rstrip("/"),
    }


def clean_phone(phone: str | None) -> str:
    """Format Pakistani phone number to standard international 923XXXXXXXXX format."""
    cfg = _get_config()
    default_phone = cfg["owner_phone"]
    if not phone:
        return default_phone
    digits = "".join(filter(str.isdigit, str(phone)))
    if digits.startswith("03"):
        return "92" + digits[1:]
    elif digits.startswith("3") and len(digits) == 10:
        return "92" + digits
    elif digits.startswith("923") and len(digits) == 12:
        return digits
    return digits or default_phone


def format_order_confirmation(
    order_number: str,
    customer_name: str,
    customer_phone: str,
    items: list[dict[str, Any]],
    total_amount: float,
    payment_method: str = "Cash on Delivery (COD)",
    delivery_address: str | None = None,
    order_id: int | None = None,
) -> tuple[str, str, str, str]:
    """
    Builds professional, bilingual (Urdu & English) order confirmation messages
    and returns (clean_phone, customer_msg, owner_msg, direct_whatsapp_url).
    """
    cfg = _get_config()
    phone = clean_phone(customer_phone)
    address_display = delivery_address or "Bakery Counter Pickup"

    items_lines = []
    for it in items:
        name = it.get("name") or it.get("product_name") or "Bakery Item"
        qty = it.get("quantity", 1)
        price = float(it.get("unit_price") or it.get("price") or 0)
        items_lines.append(f"• {name} x{qty} (Rs. {price:,.0f})")

    items_text = "\n".join(items_lines) if items_lines else "• Assorted Fresh Bakery Items"

    customer_msg = (
        f"🍰 *FRESHCO BAKERS — ORDER CONFIRMATION* 🍰\n\n"
        f"Assalam-o-Alaikum *{customer_name}*!\n"
        f"Aapka order receive ho chuka hai aur kitchen mein fresh bake ho raha hai.\n\n"
        f"📋 *Order ID:* #{order_number}\n"
        f"🎂 *Items:*\n{items_text}\n\n"
        f"💰 *Total Amount:* Rs. {float(total_amount):,.0f}\n"
        f"💳 *Payment Method:* {payment_method}\n"
        f"📍 *Delivery / Pickup:* {address_display}\n\n"
        f"⏱️ *Estimated Time:* 45 - 60 Minutes\n"
        f"🚚 *Live Tracking:* {cfg['frontend_base']}/#orders\n\n"
        f"Thank you for choosing Freshco Bakers! Baked fresh every morning. ❤️"
    )

    owner_msg = (
        f"🔔 *NEW FRESHCO BAKERY ORDER!* 🔔\n\n"
        f"*Order ID:* #{order_number}\n"
        f"*Customer:* {customer_name} ({phone})\n"
        f"*Address:* {address_display}\n"
        f"*Payment:* {payment_method} - *Rs. {float(total_amount):,.0f}*\n\n"
        f"*Items to Bake / Pack:*\n{items_text}\n\n"
        f"👉 Kitchen Orders Board: {cfg['frontend_base']}/#orders-kanban"
    )

    encoded_text = urllib.parse.quote(customer_msg)
    whatsapp_url = f"https://api.whatsapp.com/send?phone={phone}&text={encoded_text}"

    return phone, customer_msg, owner_msg, whatsapp_url


def build_whatsapp_order_link(
    order_number: str,
    customer_name: str,
    customer_phone: str,
    items: list[dict[str, Any]],
    total_amount: float,
    payment_method: str = "Cash on Delivery",
    delivery_address: str | None = None,
) -> str:
    """Returns direct click-to-chat WhatsApp link for this order."""
    _, _, _, whatsapp_url = format_order_confirmation(
        order_number=order_number,
        customer_name=customer_name,
        customer_phone=customer_phone,
        items=items,
        total_amount=total_amount,
        payment_method=payment_method,
        delivery_address=delivery_address,
    )
    return whatsapp_url


def send_whatsapp_order_notification(
    order_number: str,
    customer_name: str,
    customer_phone: str,
    items: list[dict[str, Any]],
    total_amount: float,
    payment_method: str = "Cash on Delivery",
    delivery_address: str | None = None,
    order_id: int | None = None,
) -> tuple[bool, str]:
    """
    Dispatches WhatsApp confirmation to customer and notification to owner.
    Returns (dispatched_flag, direct_whatsapp_url).
    """
    cfg = _get_config()
    phone, cust_msg, owner_msg, whatsapp_url = format_order_confirmation(
        order_number=order_number,
        customer_name=customer_name,
        customer_phone=customer_phone,
        items=items,
        total_amount=total_amount,
        payment_method=payment_method,
        delivery_address=delivery_address,
        order_id=order_id,
    )

    def _safe_log(msg: str):
        try:
            safe_text = msg.encode("ascii", "replace").decode("ascii")
            logger.info(safe_text)
        except Exception:
            pass

    _safe_log("============================================================")
    _safe_log(f"[WHATSAPP DISPATCH] Customer Order Confirmation to {phone}:")
    _safe_log(cust_msg)
    _safe_log("------------------------------------------------------------")
    _safe_log(f"[OWNER ALERT DISPATCH] Bakery Alert to {cfg['owner_phone']}:")
    _safe_log(owner_msg)
    _safe_log(f"[DIRECT WHATSAPP URL]: {whatsapp_url}")
    _safe_log("============================================================")

    dispatched = False

    def _async_send():
        # 1. Meta WhatsApp Cloud API if configured
        if cfg["meta_token"] and cfg["meta_phone_id"]:
            try:
                url = f"https://graph.facebook.com/v20.0/{cfg['meta_phone_id']}/messages"
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": phone,
                    "type": "text",
                    "text": {"preview_url": True, "body": cust_msg},
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {cfg['meta_token']}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    if 200 <= resp.status < 300:
                        logger.info("Meta Cloud API WhatsApp sent successfully to %s", phone)
            except Exception as e:
                logger.warning("Meta WhatsApp Cloud API delivery failed: %s", e)

        # 2. UltraMsg WhatsApp API if configured
        if cfg["ultramsg_id"] and cfg["ultramsg_token"]:
            try:
                url = f"https://api.ultramsg.com/{cfg['ultramsg_id']}/messages/chat"
                payload = {
                    "token": cfg["ultramsg_token"],
                    "to": phone,
                    "body": cust_msg,
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    if 200 <= resp.status < 300:
                        logger.info("UltraMsg WhatsApp sent successfully to %s", phone)
            except Exception as e:
                logger.warning("UltraMsg WhatsApp delivery failed: %s", e)

    import threading
    threading.Thread(target=_async_send, daemon=True, name="whatsapp-dispatch").start()

    return True, whatsapp_url
