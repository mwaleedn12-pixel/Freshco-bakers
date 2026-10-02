"""
Schemas for Staff & Employee Management.
"""
from pydantic import BaseModel, EmailStr, Field


class StaffCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(pattern="^(cashier|manager|admin|owner)$")


class StaffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = None
    role: str | None = Field(default=None, pattern="^(cashier|manager|admin|owner)$")
    status: str | None = Field(default=None, pattern="^(active|inactive|suspended)$")


class StaffOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None = None
    role: str
    status: str

    model_config = {"from_attributes": True}
