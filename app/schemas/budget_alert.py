from datetime import datetime

from pydantic import BaseModel


class BudgetAlertCreate(BaseModel):
    name: str
    category: str
    monthly_limit: float


class BudgetAlertUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    monthly_limit: float | None = None
    is_active: bool | None = None


class BudgetAlertResponse(BaseModel):
    id: str
    name: str
    category: str
    monthly_limit: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetAlertStatus(BaseModel):
    id: str
    name: str
    category: str
    monthly_limit: float
    spent: float
    remaining: float
    exceeded: bool
    pct_used: float
