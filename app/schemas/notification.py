from datetime import datetime

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"
    link: str | None = None


class NotificationResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    title: str
    message: str
    type: str
    is_read: bool
    link: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
