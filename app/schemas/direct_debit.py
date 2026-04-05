from datetime import datetime

from pydantic import BaseModel, model_validator


FREQUENCY_MONTHLY_FACTOR = {
    "monthly": 1.0,
    "quarterly": 1 / 3,
    "yearly": 1 / 12,
    "irregular": 1.0,  # assume monthly for irregular
}


class DirectDebitCreate(BaseModel):
    name: str
    creditor: str = ""
    mandate_reference: str | None = None
    amount: float
    currency: str = "EUR"
    frequency: str = "monthly"
    expected_day: int = 1
    account_id: str
    category_id: str | None = None
    notes: str | None = None


class DirectDebitUpdate(BaseModel):
    name: str | None = None
    creditor: str | None = None
    mandate_reference: str | None = None
    amount: float | None = None
    currency: str | None = None
    frequency: str | None = None
    expected_day: int | None = None
    category_id: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class DirectDebitResponse(BaseModel):
    id: str
    tenant_id: str
    account_id: str
    name: str
    creditor: str
    mandate_reference: str | None
    amount: float
    currency: str
    frequency: str
    expected_day: int
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
