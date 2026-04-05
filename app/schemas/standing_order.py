from datetime import date, datetime

from pydantic import BaseModel, model_validator

FREQUENCY_MONTHLY_FACTOR = {
    "monthly": 1.0,
    "biweekly": 26 / 12,  # ~2.17
    "quarterly": 1 / 3,
    "yearly": 1 / 12,
}


class StandingOrderCreate(BaseModel):
    name: str
    type: str = "expense"  # income, expense, savings_transfer
    recipient: str = ""
    amount: float
    currency: str = "EUR"
    frequency: str = "monthly"
    execution_day: int = 1
    start_date: date | None = None
    end_date: date | None = None
    account_id: str
    category_id: str | None = None
    notes: str | None = None


class StandingOrderUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    recipient: str | None = None
    amount: float | None = None
    currency: str | None = None
    frequency: str | None = None
    execution_day: int | None = None
    end_date: date | None = None
    category_id: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class StandingOrderResponse(BaseModel):
    id: str
    tenant_id: str
    account_id: str
    name: str
    type: str
    recipient: str
    amount: float
    currency: str
    frequency: str
    execution_day: int
    start_date: date
    end_date: date | None
    category_id: str | None
    is_active: bool
    notes: str | None
    created_at: datetime
    monthly_amount: float = 0.0

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def calc_monthly(cls, values):
        if hasattr(values, "__dict__"):
            amount = getattr(values, "amount", 0) or 0
            freq = getattr(values, "frequency", "monthly") or "monthly"
            factor = FREQUENCY_MONTHLY_FACTOR.get(freq, 1.0)
            values.__dict__["monthly_amount"] = round(amount * factor, 2)
        elif isinstance(values, dict):
            amount = values.get("amount", 0) or 0
            freq = values.get("frequency", "monthly") or "monthly"
            factor = FREQUENCY_MONTHLY_FACTOR.get(freq, 1.0)
            values["monthly_amount"] = round(amount * factor, 2)
        return values
