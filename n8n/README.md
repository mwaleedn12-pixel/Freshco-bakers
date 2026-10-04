# 🍰 Freshco Bakers — n8n Automation Engine

This folder contains the complete n8n automation layer for **Freshco Bakers**.

---

## 🚀 What This Automation Does

1. **New Order Placed (Website / POS / Direct Webhook)**:
   - Formats customer invoice with order number, line items, amounts, delivery address, and tracking link.
   - Sends **WhatsApp Order Confirmation** to Customer.
   - Sends **Instant Alert** to Bakery Owner & Kitchen Display via Telegram / WhatsApp.
2. **Live Order Status Updates**:
   - `CONFIRMED` ➔ "Bakery ne aapka order confirm kar liya hai! 🧑‍🍳"
   - `PREPARING` ➔ "Aapka order oven mein bake ho raha hai! 🎂🔥"
   - `READY` ➔ "Aapka order pack ho kar ready hai! 📦✨"
   - `OUT_FOR_DELIVERY` ➔ "Rider order le kar nikal chuka hai! 🛵💨"
   - `DELIVERED` ➔ "Order deliver ho gaya hai. Enjoy your treats! 🍰🎉"
3. **Low Stock Alerts**:
   - Triggers when inventory falls below minimum safety quantity (`inv.quantity <= inv.minimum_quantity`).
   - Sends urgent alert to Manager & Head Baker to restock/re-bake.
4. **Custom Cake Requests**:
   - Dispatches custom design requests & quotations to customer and decorator.
5. **Daily Sales Digest**:
   - Scheduled daily at 10:00 PM (`0 22 * * *`).
   - Sends summary of total revenue, orders, and top sellers to Bakery Owner.

---

## 📦 How to Run

### Option A: Via Main Docker Compose (Recommended)
Run from root:
```bash
docker compose up -d n8n
```
Open **n8n Web UI**: `http://localhost:5678`

### Option B: Standalone n8n
```bash
docker run -d --name freshco-n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
```

---

## 📥 How to Import Workflows in n8n

1. Open `http://localhost:5678` in your browser.
2. Complete the initial 1-minute admin setup.
3. Click **Workflows** ➔ **Add Workflow** ➔ **Import from File...** (top-right three dots menu).
4. Select `n8n/workflows/freshco_master_order_automation.json`.
5. Update your WhatsApp provider token (e.g. UltraMsg, Meta WhatsApp Cloud API, or Twilio) or Telegram Bot Token.
6. Toggle workflow to **Active**.

---

## 🧪 Testing Webhook Manually

Test order webhook from PowerShell / Terminal:
```bash
curl -X POST http://localhost:5678/webhook/freshco-events \
  -H "Content-Type: application/json" \
  -d '{
    "event": "order.created",
    "order_number": "FB-001025",
    "order_id": 1025,
    "customer": {
      "name": "Ali Khan",
      "phone": "03001234567",
      "email": "ali@example.com"
    },
    "delivery_address": "House 12, Street 4, F-7/2, Islamabad",
    "financials": {
      "subtotal": 3700,
      "discount": 0,
      "tax": 0,
      "delivery_fee": 200,
      "total_amount": 3900,
      "payment_method": "Cash on Delivery"
    },
    "items": [
      {"name": "Belgian Chocolate Cake (2 Pound)", "quantity": 1, "unit_price": 2700, "total": 2700},
      {"name": "Red Velvet Cupcakes", "quantity": 6, "unit_price": 200, "total": 1200}
    ]
  }'
```
