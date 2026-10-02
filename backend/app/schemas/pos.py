"""
Schemas for Phase 2 POS & Billing Operations.
"""
from pydantic import BaseModel, Field


class POSSaleItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    discount: float = Field(default=0.0, ge=0.0)


class POSSaleCreate(BaseModel):
    branch_id: int | None = None
    customer_id: int | None = None
    items: list[POSSaleItem]
    payment_method: str = Field(pattern="^(CASH|CARD|ONLINE|WALLET)$")
    amount_paid: float = Field(gt=0)
    notes: str | None = None


class POSReturnItem(BaseModel):
    order_item_id: int
    quantity: int = Field(gt=0)
    reason: str | None = None


class POSReturnCreate(BaseModel):
    order_id: int
    items: list[POSReturnItem]


class POSDailyClosing(BaseModel):
    branch_id: int | None = None
    cash_in_drawer: float
    card_total: float
    notes: str | None = None
