from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.coupon import CouponType


class CouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    type: CouponType
    value: float = Field(gt=0)
    min_order_amount: float | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=1)
    per_customer_limit: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    status: Literal["active", "inactive"] = "active"

    @field_validator("code")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def check(self):
        if self.type == CouponType.PERCENTAGE and self.value > 100:
            raise ValueError("Percentage discount cannot be more than 100")
        if self.starts_at and self.expires_at and self.expires_at <= self.starts_at:
            raise ValueError("expires_at must be after starts_at")
        return self


class CouponUpdate(BaseModel):
    type: CouponType | None = None
    value: float | None = Field(default=None, gt=0)
    min_order_amount: float | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=1)
    per_customer_limit: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    status: Literal["active", "inactive"] | None = None


class CouponOut(BaseModel):
    id: int
    code: str
    type: CouponType
    value: float
    min_order_amount: float | None = None
    usage_limit: int | None = None
    per_customer_limit: int | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    status: str
    times_used: int = 0

    model_config = {"from_attributes": True}


class CouponValidateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    subtotal: float = Field(gt=0)


class CouponValidateOut(BaseModel):
    code: str
    discount_amount: float
    subtotal_after_discount: float
