from pydantic import BaseModel


class WishlistItemAdd(BaseModel):
    product_id: int


class WishlistItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: float
    sale_price: float | None = None
    image_url: str | None = None
    is_available: bool
