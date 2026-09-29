from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.inventory import InventoryTransactionType


class StockAdjust(BaseModel):
    product_id: int
    branch_id: int
    # PURCHASE / RETURN add stock, WASTE removes stock (send a positive quantity for these three);
    # ADJUSTMENT is a signed correction (e.g. -3 or +5).
    type: Literal["PURCHASE", "WASTE", "ADJUSTMENT", "RETURN"]
    quantity: int = Field(ge=-100000, le=100000)


class StockTransfer(BaseModel):
    product_id: int
    from_branch_id: int
    to_branch_id: int
    quantity: int = Field(gt=0, le=100000)


class MinimumUpdate(BaseModel):
    minimum_quantity: int = Field(ge=0, le=100000)


class InventoryOut(BaseModel):
    product_id: int
    product_name: str
    sku: str
    branch_id: int
    branch_name: str
    quantity: int
    reserved_quantity: int
    available_quantity: int
    minimum_quantity: int
    is_low: bool


class InventoryPage(BaseModel):
    items: list[InventoryOut]
    total: int
    page: int
    limit: int


class TransactionOut(BaseModel):
    id: int
    product_id: int
    branch_id: int
    type: InventoryTransactionType
    quantity: int
    reference_type: str | None = None
    reference_id: int | None = None
    created_by: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    limit: int
