from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class CustomCakeCreate(BaseModel):
    type: str | None = Field(default=None, max_length=100)  # birthday / wedding / anniversary ...
    flavour: str = Field(min_length=1, max_length=100)
    size: str = Field(min_length=1, max_length=50)  # e.g. "2 lb", "serves 12"
    cream: str | None = Field(default=None, max_length=100)
    theme: str | None = Field(default=None, max_length=150)
    message: str | None = Field(default=None, max_length=200)  # text to write on the cake
    reference_image: str | None = Field(default=None, max_length=500)
    requested_date: date  # date the customer needs the cake


class CustomCakeOut(BaseModel):
    id: int
    type: str | None = None
    flavour: str | None = None
    size: str | None = None
    cream: str | None = None
    theme: str | None = None
    message: str | None = None
    reference_image: str | None = None
    requested_date: str | None = None
    quote_amount: float | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomCakeAdminOut(CustomCakeOut):
    customer_id: int
    customer_name: str | None = None
    customer_phone: str | None = None
    notes: str | None = None  # internal, never shown to customers


class CustomCakePage(BaseModel):
    items: list[CustomCakeOut]
    total: int
    page: int
    limit: int


class CustomCakeAdminPage(BaseModel):
    items: list[CustomCakeAdminOut]
    total: int
    page: int
    limit: int


class QuoteRequest(BaseModel):
    quote_amount: float = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)


class CakeStatusChange(BaseModel):
    status: Literal["in_progress", "done", "rejected", "cancelled"]
    notes: str | None = Field(default=None, max_length=1000)
