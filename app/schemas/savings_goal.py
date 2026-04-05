from datetime import date, datetime

from pydantic import BaseModel, model_validator


class SavingsGoalCreate(BaseModel):
    name: str
    type: str  # emergency, vacation_luxury, retirement
    target_amount: float
    current_amount: float = 0.0
    currency: str = "EUR"
    account_id: str | None = None
    target_date: date | None = None
    monthly_contribution: float = 0.0
    notes: str | None = None


class SavingsGoalUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    target_amount: float | None = None
    current_amount: float | None = None
    currency: str | None = None
    account_id: str | None = None
    target_date: date | None = None
    monthly_contribution: float | None = None
    notes: str | None = None
    is_active: bool | None = None


class SavingsGoalResponse(BaseModel):
    id: str
    tenant_id: str
    account_id: str | None
    name: str
    type: str
    target_amount: float
    current_amount: float
    progress_pct: float
    currency: str
    target_date: date | None
    monthly_contribution: float
    is_active: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def compute_progress(cls, values):
        if hasattr(values, "__dict__"):
            target = getattr(values, "target_amount", 0.0) or 0.0
            current = getattr(values, "current_amount", 0.0) or 0.0
        else:
            target = values.get("target_amount", 0.0) or 0.0
            current = values.get("current_amount", 0.0) or 0.0
        pct = min((current / target * 100) if target else 0.0, 100.0)
        if hasattr(values, "__dict__"):
            values.__dict__["progress_pct"] = pct
        else:
            values["progress_pct"] = pct
        return values
