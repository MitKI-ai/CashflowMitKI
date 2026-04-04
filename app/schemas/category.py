from datetime import datetime

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    color: str = "#F97316"
    icon: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    icon: str | None = None


class CategoryResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    color: str
    icon: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
