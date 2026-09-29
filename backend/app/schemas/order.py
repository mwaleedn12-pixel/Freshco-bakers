from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.order import OrderSource, OrderStatus, OrderType, PaymentMethod, PaymentStatus


class CheckoutRequest(BaseModel):
    order_type: OrderType = OrderType.PICKUP
    address_id: int | None = None  # required when order_type is DELIVERY
    branch_id: int | None = None  # defaults to the first active branch
    scheduled_at: datetime | None = None  # requested delivery/pickup time (must be in the future)
    notes: str | None = Field(default=None, max_length=500)
    coupon_code: str | None = Field(default=None, max_length=50)
    payment_method: Literal["CASH", "ONLINE"] = "CASH"


class OrderItemOut(BaseModel):
    id: int
    product_id: int | None = None
    product_name: str
    unit_price: float
    quantity: int
    discount: float
    total: float

    model_config = {"from_attributes": True}


class PaymentOut(BaseModel):
    id: int
    method: PaymentMethod
    transaction_reference: str | None = None
    amount: float
    status: PaymentStatus

    model_config = {"from_attributes": True}


class StatusHistoryOut(BaseModel):
    status: OrderStatus
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    order_number: str
    order_source: OrderSource
    order_type: OrderType
    status: OrderStatus
    payment_status: PaymentStatus
    branch_id: int | None = None
    address_id: int | None = None
    subtotal: float
    discount_total: float
    tax_total: float
    delivery_fee: float
    total: float
    scheduled_at: str | None = None
    notes: str | None = None
    created_at: datetime
    items: list[OrderItemOut] = []
    payments: list[PaymentOut] = []

    model_config = {"from_attributes": True}


class OrderDetailOut(OrderOut):
    status_history: list[StatusHistoryOut] = []


class OrderPage(BaseModel):
    items: list[OrderOut]
    total: int
    page: int
    limit: int


# ------------------------------------------------------------------ staff views
from app.schemas.address import AddressOut  # noqa: E402


class StatusChange(BaseModel):
    status: OrderStatus
    note: str | None = Field(default=None, max_length=300)


class PaymentUpdate(BaseModel):
    status: Literal["PAID", "FAILED", "REFUNDED"]
    transaction_reference: str | None = Field(default=None, max_length=150)


class OrderAdminOut(OrderOut):
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None


class OrderAdminDetailOut(OrderAdminOut):
    status_history: list[StatusHistoryOut] = []
    address: AddressOut | None = None


class OrderAdminPage(BaseModel):
    items: list[OrderAdminOut]
    total: int
    page: int
    limit: int
