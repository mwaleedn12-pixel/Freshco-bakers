"""
Schemas for Bakery Application Settings.
"""
from typing import Any
from pydantic import BaseModel


class SettingItem(BaseModel):
    key: str
    value: Any = None
    category: str = "general"

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    key: str
    value: Any = None
    category: str = "general"


class SettingsBulkUpdate(BaseModel):
    settings: list[SettingUpdate]
