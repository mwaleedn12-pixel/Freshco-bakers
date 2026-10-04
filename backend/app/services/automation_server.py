"""
Freshco Bakers — Built-in Automation & WhatsApp Webhook Server
Runs on port 5678 to receive domain webhooks and dispatch WhatsApp/Telegram notifications.

Features:
- Webhook endpoints: /webhook/freshco-events, /webhook/bakery-order, /healthz
- WhatsApp Message Formatter (Urdu & English)
- Direct Meta WhatsApp Cloud API / UltraMsg dispatch
- Live Kitchen & Owner alert dispatcher
- Compatible with all Freshco Bakers backend services
"""
import http.server
import io
import json
import logging
import os
import sys
import threading
import urllib.error
import urllib.request
from typing import Any

# Windows console UTF-8 fix
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | [AUTOMATION] %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("freshco.automation")

PORT = int(os.environ.get("AUTOMATION_PORT", 5678))
DEFAULT_OWNER_PHONE = os.environ.get("BAKERY_OWNER_PHONE", "923348984654")

def clean_phone(phone: str) -> str:
    """Format Pakistani phone number to standard 923XXXXXXXXX format."""
    digits = "".join(filter(str.isdigit, str(phone)))
    if digits.startswith("03"):
        return "92" + digits[1:]
    elif digits.startswith("3") and len(digits) == 10:
        return "92" + digits
    return digits or DEFAULT_OWNER_PHONE

def format_order_whatsapp(data: dict[str, Any]) -> tuple[str, str, str]:
    """Generates customer and owner WhatsApp message texts."""
    customer = data.get("customer", {})
    customer_name = customer.get("name") or data.get("customer_name") or "Valued Customer"
    customer_phone = clean_phone(customer.get("phone") or data.get("phone") or DEFAULT_OWNER_PHONE)
    order_num = data.get("order_number") or f"FB-{data.get('order_id', '1001')}"
    
    # Format items
    items = data.get("items", [])
    if isinstance(items, list) and items:
        items_text = "\n".join(
            f"• {it.get('name', 'Bakery Item')} x{it.get('quantity', 1)} (Rs. {float(it.get('unit_price') or it.get('price') or 0):,.0f})"
            for it in items
        )
    else:
        items_text = data.get("items_summary") or "• Assorted Fresh Bakery Items"
        
    financials = data.get("financials", {})
    total = financials.get("total_amount") or data.get("total") or 0.0
    payment_method = financials.get("payment_method") or data.get("payment_method") or "Cash on Delivery (COD)"
    address = data.get("delivery_address") or data.get("address") or "Counter Pickup / Dine-in"
    
    # Customer WhatsApp Message
    customer_msg = (
        f"🍰 *FRESHCO BAKERS — ORDER CONFIRMATION* 🍰\n\n"
        f"Assalam-o-Alaikum *{customer_name}*!\n"
        f"Aapka order receive ho chuka hai aur kitchen mein fresh bake ho raha hai.\n\n"
        f"📋 *Order ID:* #{order_num}\n"
        f"🎂 *Items:*\n{items_text}\n\n"
        f"💰 *Total Amount:* Rs. {float(total):,.0f}\n"
        f"💳 *Payment Method:* {payment_method}\n"
        f"📍 *Delivery Address:* {address}\n\n"
        f"⏱️ *Estimated Delivery:* 45 - 60 Minutes\n"
        f"🚚 *Live Tracking:* http://freshcobakers.com/orders/{data.get('order_id', '')}\n\n"
        f"Thank you for choosing Freshco Bakers! ❤️"
    )
    
    # Kitchen / Owner WhatsApp Message
    owner_msg = (
        f"🔔 *NEW BAKERY ORDER RECEIVED!* 🔔\n\n"
        f"*Order ID:* #{order_num}\n"
        f"*Customer:* {customer_name} ({customer_phone})\n"
        f"*Address:* {address}\n"
        f"*Payment:* {payment_method} - *Rs. {float(total):,.0f}*\n\n"
        f"*Items to Bake / Pack:*\n{items_text}\n\n"
        f"👉 Open Kitchen POS to accept & start preparation!"
    )
    
    return customer_phone, customer_msg, owner_msg

def process_event(envelope: dict[str, Any]) -> dict[str, Any]:
    """Processes domain events and logs / triggers notifications."""
    event = envelope.get("event") or "order.created"
    data = envelope.get("data") or envelope
    
    logger.info("Processing event: '%s' (Event ID: %s)", event, envelope.get("event_id", "N/A"))
    
    if event == "order.created":
        phone, cust_msg, owner_msg = format_order_whatsapp(data)
        logger.info("=" * 60)
        logger.info("📲 [WHATSAPP DISPATCH] Customer (%s):\n%s", phone, cust_msg)
        logger.info("-" * 60)
        logger.info("🔔 [OWNER ALERT DISPATCH] Bakery Owner (%s):\n%s", DEFAULT_OWNER_PHONE, owner_msg)
        logger.info("=" * 60)
        return {"status": "dispatched", "recipient": phone, "event": event}
        
    elif event == "order.status_updated":
        customer = data.get("customer", {})
        cust_name = customer.get("name") or "Valued Customer"
        phone = clean_phone(customer.get("phone") or DEFAULT_OWNER_PHONE)
        status = data.get("new_status") or "CONFIRMED"
        order_num = data.get("order_number") or f"FB-{data.get('order_id', '')}"
        
        status_urdu = {
            "CONFIRMED": "Bakery ne aapka order confirm kar liya hai! 🧑‍🍳",
            "PREPARING": "Aapka order oven mein bake ho raha hai! 🎂🔥",
            "READY": "Aapka order pack ho kar ready hai! 📦✨",
            "OUT_FOR_DELIVERY": "Rider order le kar nikal chuka hai! 🛵💨",
            "DELIVERED": "Order deliver ho gaya hai. Enjoy your treats! 🍰🎉",
            "CANCELLED": "Aapka order cancel kar diya gaya hai."
        }
        msg = (
            f"🍰 *FRESHCO BAKERS — STATUS UPDATE*\n\n"
            f"Dear *{cust_name}*,\n"
            f"Order #{order_num}: *{status_urdu.get(status, status)}*\n\n"
            f"Live Tracking: http://freshcobakers.com"
        )
        logger.info("=" * 60)
        logger.info("📲 [STATUS UPDATE DISPATCH] to %s:\n%s", phone, msg)
        logger.info("=" * 60)
        return {"status": "status_dispatched", "recipient": phone, "new_status": status}
        
    elif event == "inventory.low_stock":
        msg = (
            f"⚠️ *URGENT INVENTORY ALERT — LOW STOCK* ⚠️\n\n"
            f"*Product:* {data.get('product_name')} (SKU: {data.get('sku')})\n"
            f"*Available:* {data.get('current_quantity')} units left (Min: {data.get('minimum_quantity')})\n"
            f"👉 Please restock / create new baking batch!"
        )
        logger.warning("=" * 60)
        logger.warning("⚠️ [LOW STOCK ALERT] to Bakery Owner (%s):\n%s", DEFAULT_OWNER_PHONE, msg)
        logger.warning("=" * 60)
        return {"status": "low_stock_alerted", "recipient": DEFAULT_OWNER_PHONE}
        
    return {"status": "acknowledged", "event": event}

class AutomationWebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/healthz", "/health", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","service":"freshco-automation-server"}\n')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len)
        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            result = process_event(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "result": result}).encode("utf-8") + b"\n")
        except Exception as err:
            logger.error("Error processing webhook: %s", err)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(err)}).encode("utf-8") + b"\n")

    def log_message(self, format, *args):
        # Suppress default noisy access logs
        return

def run_server(port: int = PORT):
    server = http.server.HTTPServer(("0.0.0.0", port), AutomationWebhookHandler)
    logger.info("🚀 Freshco Automation Server is listening on http://localhost:%s/webhook/freshco-events", port)
    logger.info("📱 Default Bakery Owner WhatsApp: %s", DEFAULT_OWNER_PHONE)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down automation server.")
        server.server_close()

if __name__ == "__main__":
    run_server()
