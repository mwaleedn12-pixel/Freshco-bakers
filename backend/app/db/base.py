"""
Declarative base shared by every ORM model.
Import every model module here so Alembic autogenerate can see them
(models are added module-by-module as we build out the schema).
"""
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    pass


# --- model imports: every table must be imported here so Alembic autogenerate
# and Base.metadata.create_all() can discover it ---
from app.models.user import User, Role, Permission, RolePermission  # noqa: E402,F401
from app.models.branch import Branch, Address  # noqa: E402,F401
from app.models.catalog import Category, Product, ProductImage  # noqa: E402,F401
from app.models.cart import Cart, CartItem  # noqa: E402,F401
from app.models.order import Order, OrderItem, Payment, OrderStatusHistory  # noqa: E402,F401
from app.models.custom_cake import CustomCakeRequest  # noqa: E402,F401
from app.models.review import Review  # noqa: E402,F401
from app.models.wishlist import Wishlist, WishlistItem  # noqa: E402,F401
from app.models.coupon import Coupon, CouponUsage  # noqa: E402,F401
from app.models.inventory import Inventory, InventoryTransaction  # noqa: E402,F401
from app.models.notification import Notification  # noqa: E402,F401
from app.models.expense import Expense  # noqa: E402,F401
from app.models.return_ import Return  # noqa: E402,F401
from app.models.audit_log import AuditLog  # noqa: E402,F401
from app.models.setting import Setting  # noqa: E402,F401
