"""
Seed Script — Populates Freshco Bakers database with realistic demo data.
Includes Users, Branches, Categories, Products, Inventory, Orders, POS Sales, Coupons, Custom Cakes, Reviews & Expenses.
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.branch import Branch
from app.models.catalog import Category, Product
from app.models.coupon import Coupon, CouponType
from app.models.custom_cake import CustomCakeRequest
from app.models.expense import Expense
from app.models.inventory import Inventory, InventoryTransaction, InventoryTransactionType
from app.models.order import (
    Order, OrderItem, OrderSource, OrderStatus, OrderType, Payment, PaymentMethod, PaymentStatus,
)
from app.models.review import Review
from app.models.setting import Setting
from app.models.user import Role, User


def seed_data():
    db: Session = SessionLocal()
    try:
        print("[+] Seeding Freshco Bakers Demo Data...")

        # 1. Roles
        role_names = ["customer", "cashier", "manager", "admin", "owner"]
        roles = {}
        for rname in role_names:
            role = db.query(Role).filter(Role.name == rname).first()
            if not role:
                role = Role(name=rname, description=f"{rname.capitalize()} role")
                db.add(role)
                db.flush()
            roles[rname] = role

        # 2. Users
        def get_or_create_user(name, email, role_name, phone=None):
            u = db.query(User).filter(User.email == email).first()
            if not u:
                u = User(
                    name=name,
                    email=email,
                    phone=phone or "+923001234567",
                    password_hash=hash_password("password123"),
                    role_id=roles[role_name].id,
                    status="active",
                )
                db.add(u)
                db.flush()
            return u

        owner = get_or_create_user("Waleed Owner", "owner@freshco.com", "owner", "+923000000001")
        get_or_create_user("Admin User", "admin@freshco.com", "admin", "+923000000002")
        manager = get_or_create_user("Zain Manager", "manager@freshco.com", "manager", "+923000000003")
        get_or_create_user("Ali Cashier", "cashier@freshco.com", "cashier", "+923000000004")
        cust1 = get_or_create_user("Sara Ahmed", "sara@gmail.com", "customer", "+923111111111")
        cust2 = get_or_create_user("Hamza Khan", "hamza@gmail.com", "customer", "+923222222222")



        # 3. Branches
        b_main = db.query(Branch).filter(Branch.code == "MAIN").first()
        if not b_main:
            b_main = Branch(name="Gulberg Main Bakery", code="MAIN", city="Lahore", phone="+92423555111")
            db.add(b_main)
            db.flush()

        b_dha = db.query(Branch).filter(Branch.code == "DHA5").first()
        if not b_dha:
            b_dha = Branch(name="DHA Phase 5 Outlet", code="DHA5", city="Lahore", phone="+92423555222")
            db.add(b_dha)
            db.flush()

        # 4. Categories
        cat_data = [
            ("Breads & Sourdough", "Artisan fermented loaves & rustic rolls"),
            ("Celebration Cakes", "Gourmet fudge, velvet, & layered cakes"),
            ("French Pastries", "Butter croissants, danishes & tarts"),
            ("Cookies & Brownies", "Double chocolate, biscoff & chunk cookies"),
            ("Savory Bakes", "Puff pastries, quiches & chicken pies"),
        ]
        categories = {}
        for cname, _ in cat_data:
            c = db.query(Category).filter(Category.name == cname).first()
            if not c:
                c_slug = cname.lower().replace("&", "and").replace(" ", "-").replace("--", "-")
                c = Category(name=cname, slug=c_slug, status="active")
                db.add(c)
                db.flush()
            categories[cname] = c


        # 5. Products
        prod_list = [
            {
                "sku": "SD-001",
                "barcode": "890123456001",
                "name": "Artisanal Sourdough Loaf",
                "description": "Naturally fermented for 24h with a golden crispy crust and soft airy crumb.",
                "price": 450.0,
                "sale_price": 400.0,
                "cost_price": 220.0,
                "cat": "Breads & Sourdough",
            },
            {
                "sku": "CK-002",
                "barcode": "890123456002",
                "name": "Belgian Chocolate Fudge Cake",
                "description": "Layers of rich dark Belgian chocolate fudge and silky chocolate ganache.",
                "price": 1800.0,
                "sale_price": 1650.0,
                "cost_price": 900.0,
                "cat": "Celebration Cakes",
            },
            {
                "sku": "PS-003",
                "barcode": "890123456003",
                "name": "Butter Croissant Box (6)",
                "description": "81-layer flaky French butter croissants baked golden every morning.",
                "price": 900.0,
                "sale_price": None,
                "cost_price": 400.0,
                "cat": "French Pastries",
            },
            {
                "sku": "CK-004",
                "barcode": "890123456004",
                "name": "Red Velvet Supreme Cake",
                "description": "Classic velvet sponge layered with smooth vanilla bean cream cheese frosting.",
                "price": 2200.0,
                "sale_price": 1950.0,
                "cost_price": 1100.0,
                "cat": "Celebration Cakes",
            },
            {
                "sku": "PS-005",
                "barcode": "890123456005",
                "name": "Almond Croissant",
                "description": "Filled with rich almond frangipane cream and topped with toasted almonds.",
                "price": 320.0,
                "sale_price": None,
                "cost_price": 150.0,
                "cat": "French Pastries",
            },
            {
                "sku": "CK-006",
                "barcode": "890123456006",
                "name": "Lotus Biscoff Cheesecake Slice",
                "description": "Creamy baked cheesecake with a crunchy Biscoff biscuit base & Lotus drip.",
                "price": 550.0,
                "sale_price": None,
                "cost_price": 250.0,
                "cat": "Celebration Cakes",
            },
            {
                "sku": "CK-007",
                "barcode": "890123456007",
                "name": "Double Chocolate Chunk Cookie",
                "description": "Gooey warm cookie loaded with Belgian dark and milk chocolate chunks.",
                "price": 180.0,
                "sale_price": None,
                "cost_price": 80.0,
                "cat": "Cookies & Brownies",
            },
            {
                "sku": "SV-008",
                "barcode": "890123456008",
                "name": "Chicken Puff Pastry",
                "description": "Golden flaky puff pastry filled with seasoned shredded chicken and spices.",
                "price": 220.0,
                "sale_price": None,
                "cost_price": 100.0,
                "cat": "Savory Bakes",
            },
        ]

        products = []
        for pdata in prod_list:
            p = db.query(Product).filter(Product.sku == pdata["sku"]).first()
            if not p:
                p_slug = pdata["name"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "and")
                p = Product(
                    sku=pdata["sku"],
                    barcode=pdata["barcode"],
                    name=pdata["name"],
                    slug=p_slug,
                    description=pdata["description"],
                    price=pdata["price"],
                    sale_price=pdata["sale_price"],
                    cost_price=pdata["cost_price"],
                    category_id=categories[pdata["cat"]].id,
                    status="active",
                    is_featured=True,
                )
                db.add(p)
                db.flush()


                # Add stock to branch
                inv = Inventory(product_id=p.id, branch_id=b_main.id, quantity=30, minimum_quantity=5)
                db.add(inv)

                inv_tx = InventoryTransaction(
                    product_id=p.id,
                    branch_id=b_main.id,
                    type=InventoryTransactionType.PURCHASE,
                    quantity=30,
                    reference_type="INITIAL_STOCK",
                    created_by=owner.id,
                )
                db.add(inv_tx)

            products.append(p)

        # 6. Settings
        settings_defaults = [
            ("bakery.name", "Freshco Bakers"),
            ("bakery.tagline", "Freshness Baked Daily in 3D Style"),
            ("delivery.fee_flat", 150.0),
            ("tax.rate_percent", 5.0),
        ]
        for skey, sval in settings_defaults:
            s = db.query(Setting).filter(Setting.key == skey).first()
            if not s:
                db.add(Setting(key=skey, value=sval, category="general"))

        # 7. Coupons
        c1 = db.query(Coupon).filter(Coupon.code == "WELCOME10").first()
        if not c1:
            db.add(Coupon(code="WELCOME10", type=CouponType.PERCENTAGE, value=10.0, status="active"))

        # 8. Sample Web Orders & POS Sales
        # Web Order 1
        ord1 = db.query(Order).filter(Order.order_number == "FB-2026-8812").first()
        if not ord1:
            ord1 = Order(
                order_number="FB-2026-8812",
                customer_id=cust1.id,
                branch_id=b_main.id,
                order_source=OrderSource.WEBSITE,
                order_type=OrderType.DELIVERY,
                status=OrderStatus.OUT_FOR_DELIVERY,
                payment_status=PaymentStatus.PAID,
                subtotal=2050.0,
                discount_total=100.0,
                tax_total=97.5,
                delivery_fee=150.0,
                total=2197.5,
                notes="Leave at front gate please",
            )
            db.add(ord1)
            db.flush()

            db.add(OrderItem(order_id=ord1.id, product_id=products[1].id, product_name=products[1].name, unit_price=1650.0, quantity=1, total=1650.0))
            db.add(OrderItem(order_id=ord1.id, product_id=products[0].id, product_name=products[0].name, unit_price=400.0, quantity=1, total=400.0))
            db.add(Payment(order_id=ord1.id, method=PaymentMethod.CARD, amount=2197.5, status=PaymentStatus.PAID, transaction_reference="TXN-CARD-991"))

        # POS Counter Sale
        pos1 = db.query(Order).filter(Order.order_number == "POS-2026-9001").first()
        if not pos1:
            pos1 = Order(
                order_number="POS-2026-9001",
                customer_id=None,
                branch_id=b_main.id,
                order_source=OrderSource.POS,
                order_type=OrderType.PICKUP,
                status=OrderStatus.DELIVERED,
                payment_status=PaymentStatus.PAID,
                subtotal=1120.0,
                discount_total=0.0,
                tax_total=56.0,
                delivery_fee=0.0,
                total=1176.0,
            )
            db.add(pos1)
            db.flush()

            db.add(OrderItem(order_id=pos1.id, product_id=products[2].id, product_name=products[2].name, unit_price=900.0, quantity=1, total=900.0))
            db.add(OrderItem(order_id=pos1.id, product_id=products[7].id, product_name=products[7].name, unit_price=220.0, quantity=1, total=220.0))
            db.add(Payment(order_id=pos1.id, method=PaymentMethod.CASH, amount=1176.0, status=PaymentStatus.PAID, transaction_reference="POS-CASH-881"))

        # 9. Custom Cake Request
        cake_req = db.query(CustomCakeRequest).filter(CustomCakeRequest.customer_id == cust1.id).first()
        if not cake_req:
            db.add(
                CustomCakeRequest(
                    customer_id=cust1.id,
                    type="Birthday Tier Cake",
                    flavour="Belgian Chocolate & Caramel",
                    size="4 Lbs",
                    cream="Buttercream",
                    theme="Gold 21st Celebration",
                    message="Happy 21st Birthday Sara!",
                    quote_amount=4500.0,
                    status="quoted",
                )
            )

        # 10. Reviews
        rev1 = db.query(Review).filter(Review.customer_id == cust1.id).first()
        if not rev1:
            db.add(
                Review(
                    customer_id=cust1.id,
                    product_id=products[1].id,
                    rating=5,
                    comment="The Belgian Chocolate Fudge Cake was absolutely incredible! Delivered fresh and soft.",
                    status="approved",
                )
            )
            db.add(
                Review(
                    customer_id=cust2.id,
                    product_id=products[0].id,
                    rating=5,
                    comment="Best sourdough loaf in Lahore. Perfect crunch and texture.",
                    status="approved",
                )
            )

        # 11. Expenses
        exp1 = db.query(Expense).filter(Expense.description == "September Electricity & Gas Bill").first()
        if not exp1:
            db.add(
                Expense(
                    branch_id=b_main.id,
                    category="Utilities",
                    description="September Electricity & Gas Bill",
                    amount=45000.0,
                    expense_date="2026-10-01",
                    created_by=manager.id,
                )
            )
            db.add(
                Expense(
                    branch_id=b_main.id,
                    category="Ingredients",
                    description="Flour, Butter & Chocolate Supply",
                    amount=85000.0,
                    expense_date="2026-10-02",
                    created_by=manager.id,
                )
            )

        db.commit()
        print("[SUCCESS] Demo Data Seeded Successfully!")
        print("\n[KEYS] Login Credentials Created:")
        print("   Owner:    owner@freshco.com   / password123")
        print("   Admin:    admin@freshco.com   / password123")
        print("   Manager:  manager@freshco.com / password123")
        print("   Cashier:  cashier@freshco.com / password123")
        print("   Customer: sara@gmail.com      / password123")

    except Exception as e:
        db.rollback()
        print("[ERROR] Seeding Error:", e)
    finally:
        db.close()



if __name__ == "__main__":
    seed_data()
