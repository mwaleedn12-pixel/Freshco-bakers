from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ModerateRequest(BaseModel):
    status: Literal["approved", "rejected", "pending"]


class ReviewOut(BaseModel):
    id: int
    product_id: int
    rating: int
    comment: str | None = None
    status: str
    customer_name: str | None = None  # first name only on public views
    created_at: datetime


class ReviewPage(BaseModel):
    items: list[ReviewOut]
    total: int
    page: int
    limit: int


class ProductReviews(BaseModel):
    product_id: int
    average_rating: float
    review_count: int
    distribution: dict[str, int]  # {"1": n, ..., "5": n}
    items: list[ReviewOut]
    page: int
    limit: int
