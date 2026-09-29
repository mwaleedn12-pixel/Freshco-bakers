"""
Schemas for categories, products and product images.
ProductOut (public) never exposes cost_price; ProductAdminOut does.
"""
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["active", "inactive"]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    parent_id: int | None = None
    sort_order: int = 0
    status: Status = "active"


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    parent_id: int | None = None
    sort_order: int | None = None
    status: Status | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: int | None = None
    sort_order: int
    status: str

    model_config = {"from_attributes": True}


class ProductImageCreate(BaseModel):
    image_url: str = Field(min_length=1, max_length=500)
    sort_order: int = 0
    is_primary: bool = False


class ProductImageOut(BaseModel):
    id: int
    image_url: str
    sort_order: int
    is_primary: bool

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    barcode: str | None = Field(default=None, max_length=50)
    category_id: int | None = None
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: float = Field(gt=0)
    sale_price: float | None = Field(default=None, gt=0)
    cost_price: float | None = Field(default=None, ge=0)
    is_featured: bool = False
    is_available: bool = True
    track_inventory: bool = True


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    barcode: str | None = Field(default=None, max_length=50)
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    sale_price: float | None = Field(default=None, gt=0)
    cost_price: float | None = Field(default=None, ge=0)
    is_featured: bool | None = None
    is_available: bool | None = None
    track_inventory: bool | None = None
    status: Literal["active", "inactive", "archived"] | None = None


class ProductOut(BaseModel):
    id: int
    sku: str
    barcode: str | None = None
    category_id: int | None = None
    name: str
    slug: str
    description: str | None = None
    price: float
    sale_price: float | None = None
    is_featured: bool
    is_available: bool
    images: list[ProductImageOut] = []

    model_config = {"from_attributes": True}


class ProductAdminOut(ProductOut):
    cost_price: float | None = None
    track_inventory: bool
    status: str


class ProductPage(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    limit: int


class ProductAdminPage(BaseModel):
    items: list[ProductAdminOut]
    total: int
    page: int
    limit: int
