from datetime import time
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BranchCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=20)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    opening_time: time | None = None
    closing_time: time | None = None
    status: Literal["active", "inactive"] = "active"

    @field_validator("code")
    @classmethod
    def upper_code(cls, v: str) -> str:
        return v.strip().upper()


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    code: str | None = Field(default=None, min_length=2, max_length=20)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    opening_time: time | None = None
    closing_time: time | None = None
    status: Literal["active", "inactive"] | None = None

    @field_validator("code")
    @classmethod
    def upper_code(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else v


class BranchOut(BaseModel):
    id: int
    name: str
    code: str
    address: str | None = None
    city: str | None = None
    phone: str | None = None
    opening_time: time | None = None
    closing_time: time | None = None
    status: str

    model_config = {"from_attributes": True}
