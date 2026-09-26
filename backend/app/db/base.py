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


# --- model imports go here as each module is built ---
# from app.models.user import User
# from app.models.product import Product
# from app.models.order import Order
