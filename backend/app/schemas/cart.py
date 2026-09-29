from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CartItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    line_total: float
    is_available: bool


class CartOut(BaseModel):
    id: int
    items: list[CartItemOut]
    item_count: int
    subtotal: float
