import io
import json
import sys
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Test configuration
PHONE_NUMBER = "923348984654"
CUSTOMER_NAME = "M. Waleed"
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/freshco-events"

payload = {
    "event": "order.created",
    "order_number": "FB-001025",
    "order_id": 1025,
    "customer": {
        "name": CUSTOMER_NAME,
        "phone": PHONE_NUMBER,
        "email": "waleed@example.com"
    },
    "delivery_address": "House 12, Street 4, Islamabad",
    "financials": {
        "subtotal": 3700.0,
        "discount": 0.0,
        "tax": 0.0,
        "delivery_fee": 200.0,
        "total_amount": 3900.0,
        "payment_method": "Cash on Delivery"
    },
    "items": [
        {"name": "Belgian Chocolate Cake (2 Lbs)", "quantity": 1, "unit_price": 2500.0, "total": 2500.0},
        {"name": "Red Velvet Cupcakes", "quantity": 6, "unit_price": 200.0, "total": 1200.0}
    ]
}

def test_n8n():
    print(f"[>] Sending test bakery order for {CUSTOMER_NAME} ({PHONE_NUMBER})...")
    print(f"[>] Target Webhook: {N8N_WEBHOOK_URL}")
    data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        N8N_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            print(f"[+] Webhook received successfully! HTTP Status: {resp.status}")
            print(f"[+] n8n is now processing WhatsApp notification to: {PHONE_NUMBER}")
            print("[+] Sample Message Dispatched:")
            print("--------------------------------------------------")
            print(f"Freshco Bakers Order #FB-001025 received for {CUSTOMER_NAME}!")
            print(f"Items: Belgian Chocolate Cake (2 Lbs) x1, Red Velvet Cupcakes x6")
            print(f"Total: Rs. 3,900 | COD | Address: House 12, Street 4, Islamabad")
            print("--------------------------------------------------")
    except urllib.error.URLError as e:
        print(f"[!] Note: Could not connect to local n8n container ({e.reason})")
        print("[i] If you haven't started n8n yet, run:")
        print("    docker compose up -d n8n")
        print("    Then open: http://localhost:5678")

if __name__ == "__main__":
    test_n8n()
