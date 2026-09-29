from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str | None = None
    type: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    total: int
    unread_count: int
    page: int
    limit: int
