from datetime import datetime

from pydantic import BaseModel


class SnapshotCreate(BaseModel):
    month: str  # YYYY-MM


class SnapshotResponse(BaseModel):
    id: str
    month: str
    monthly_income: float
    monthly_expenses: float
    monthly_direct_debits: float
    monthly_subscriptions: float
    monthly_savings: float
    monthly_net: float
    net_worth: float
    created_at: datetime

    model_config = {"from_attributes": True}


class TrendResponse(BaseModel):
    months: list[str]
    income: list[float]
    expenses: list[float]
    net: list[float]
    net_worth: list[float]
