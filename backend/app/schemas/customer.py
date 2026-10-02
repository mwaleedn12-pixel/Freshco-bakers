"""
Schemas for Customer Profiles & Lifetime Metrics.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.schemas.address import AddressOut


class CustomerOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None = None
    status: str
    total_orders: int = 0
    total_spend: float = 0.0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CustomerDetailOut(CustomerOut):
    addresses: list[AddressOut] = []
