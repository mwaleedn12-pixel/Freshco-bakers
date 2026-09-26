"""
Model integration test: builds the schema in-memory (SQLite) and exercises
relationships across the core Freshco Bakers flow — role -> user -> category
-> product -> order -> order_item -> payment.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.catalog import Category, Product
from app.models.order import Order, OrderItem, OrderSource, Payment, PaymentMethod, PaymentStatus
from app.models.user import Role, User


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_full_relationship_chain():
    session = make_session()

    role = Role(name="customer", description="Website customer")
    session.add(role)
    session.flush()

    user = User(
        name="Ayesha Khan",
        email="ayesha@example.com",
        password_hash="hashed-value",
        role_id=role.id,
    )
    session.add(user)
    session.flush()

    category = Category(name="Cakes", slug="cakes")
    session.add(category)
    session.flush()

    product = Product(
        sku="CAKE-001",
        category_id=category.id,
        name="Chocolate Fudge Cake",
        slug="chocolate-fudge-cake",
        price=1800,
        cost_price=900,
    )
    session.add(product)
    session.flush()

    order = Order(
        order_number="FB-000001",
        customer_id=user.id,
        order_source=OrderSource.WEBSITE,
        subtotal=1800,
        total=1800,
    )
    session.add(order)
    session.flush()

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.name,  # snapshot
        unit_price=product.price,
        quantity=1,
        total=1800,
    )
    payment = Payment(
        order_id=order.id,
        method=PaymentMethod.CARD,
        amount=1800,
        status=PaymentStatus.PAID,
    )
    session.add_all([order_item, payment])
    session.commit()

    # Re-fetch and verify relationships resolve correctly
    fetched_order = session.get(Order, order.id)
    assert fetched_order is not None
    assert len(fetched_order.items) == 1
    assert fetched_order.items[0].product_name == "Chocolate Fudge Cake"
    assert len(fetched_order.payments) == 1
    assert fetched_order.payments[0].status == PaymentStatus.PAID
    assert fetched_order.order_source == OrderSource.WEBSITE

    session.close()
