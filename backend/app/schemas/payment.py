"""
Schemas for Payment Processing & Receipt Generation.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class PaymentProcessRequest(BaseModel):
    order_id: int
    method: str = Field(pattern="^(CASH|CARD|ONLINE|WALLET)$")
    amount: float = Field(gt=0)
    transaction_reference: str | None = None


class PaymentOut(BaseModel):
    id: int
    order_id: int
    method: str
    amount: float
    status: str
    transaction_reference: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReceiptItemOut(BaseModel):
    product_name: str
    quantity: int
    unit_price: float
    total: float


class ThermalReceiptOut(BaseModel):
    bakery_name: str
    order_number: str
    order_source: str
    order_type: str
    created_at: str
    items: list[ReceiptItemOut]
    subtotal: float
    discount_total: float
    tax_total: float
    delivery_fee: float
    total: float
    payment_status: str
    payment_method: str | None = None
