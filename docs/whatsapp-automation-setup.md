# 📱 WhatsApp Automation Setup Guide — Freshco Bakers

Freshco Bakers ke liye **WhatsApp Automation** 3 mukhtalif tareeqon se lag sakti hai. Aap apni zaroorat ke hisaab se koi bhi option choose kar sakte hain:

---

## 🏆 Option 1: Meta Official WhatsApp Cloud API (Recommended & Official)
> **Khasiyat:** Official Meta API, safe (number ban ka koi khatra nahi), **har maheene 1,000 Service conversations FREE**.

### Setup Steps:
1. [developers.facebook.com](https://developers.facebook.com/) par account banayein.
2. **Create App** ➔ Type **Business** select karein.
3. Dashboard se **WhatsApp** add karein.
4. Wahan se aapko 3 cheezein milengi:
   - **Phone Number ID** (e.g. `105938271829102`)
   - **WhatsApp Business Account ID**
   - **Temporary / Permanent Access Token**
5. Apne `.env` ya n8n workflow node mein ye values daal dein:
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_ACCESS_TOKEN`

---

## ⚡ Option 2: UltraMsg / Green API (Fastest — 1 Minute QR Code Setup)
> **Khasiyat:** Koi developer account ya approval nahi chahiye. Apne bakery ke existing mobile number se WhatsApp Web ki tarah **QR code scan** karein aur foran shuru ho jayein.

### Setup Steps:
1. [ultramsg.com](https://ultramsg.com/) par account banayein.
2. **Instance Create** karein aur WhatsApp mobile app se **QR Code scan** karein.
3. Aapko milega:
   - **Instance ID** (e.g. `instance12345`)
   - **Token** (e.g. `abcde12345token`)
4. n8n workflow mein UltraMsg node mein token paste karein.

---

## 🆓 Option 3: Evolution API / Baileys (100% Free Self-Hosted Docker)
> **Khasiyat:** 100% Free, unlimited messages, zero monthly charges.

### Setup via Docker Compose:
`docker-compose.yml` mein Evolution API service add kar ke bakery number QR code se connect kiya ja sakta hai.

---

## 💬 Automated Message Templates Included

### 1. Order Confirmation Message (Customer):
```text
🍰 *FRESHCO BAKERS — ORDER CONFIRMATION* 🍰

Assalam-o-Alaikum *Ali Khan*!
Aapka order receive ho chuka hai aur kitchen mein process ho raha hai.

📋 *Order ID:* #FB-001025
🎂 *Items:*
• Belgian Chocolate Cake (2 Lbs) x1 (Rs. 2,500)
• Red Velvet Cupcakes x6 (Rs. 1,200)

💰 *Total Amount:* Rs. 3,900
💳 *Payment Method:* Cash on Delivery (COD)
📍 *Delivery Address:* House 12, Street 4, F-7/2, Islamabad

⏱️ *Estimated Time:* 45 - 60 Minutes
🚚 *Live Tracking:* https://freshcobakers.com/orders/1025

Fresh bakes, always fresh taste! ❤️
```

### 2. Kitchen / Owner Alert Message:
```text
🔔 *NEW BAKERY ORDER RECEIVED!* 🔔

*Order ID:* #FB-001025
*Customer:* Ali Khan (03001234567)
*Type / Address:* House 12, Street 4, F-7/2, Islamabad
*Payment:* Cash on Delivery - *Rs. 3,900*

*Order Details:*
• Belgian Chocolate Cake x1
• Red Velvet Cupcakes x6

👉 Kitchen POS par accept kar ke baking start karein!
```

### 3. Live Status Update Messages (Auto Triggered):
- **CONFIRMED:** `Bakery ne aapka order confirm kar liya hai! 🧑‍🍳`
- **PREPARING:** `Aapka order oven mein bake / prepare ho raha hai! 🎂🔥`
- **READY:** `Aapka order pack ho kar ready hai! 📦✨`
- **OUT FOR DELIVERY:** `Rider order le kar nikal chuka hai! 🛵💨`
- **DELIVERED:** `Order deliver ho gaya hai. Enjoy your delicious treats! 🍰🎉`
