from datetime import datetime

from pydantic import BaseModel, model_validator


class InvestmentCreate(BaseModel):
    name: str
    type: str
    account_id: str | None = None
    broker: str = ""
    isin: str | None = None
    currency: str = "EUR"
    current_value: float = 0.0
    invested_amount: float = 0.0
    quantity: float | None = None
    purchase_price: float | None = None
    notes: str | None = None


class InvestmentUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    account_id: str | None = None
    broker: str | None = None
    isin: str | None = None
    currency: str | None = None
    current_value: float | None = None
    invested_amount: float | None = None
    quantity: float | None = None
    purchase_price: float | None = None
    notes: str | None = None
    is_active: bool | None = None


class InvestmentResponse(BaseModel):
    id: str
    tenant_id: str
    account_id: str | None
    name: str
    type: str
    broker: str
    isin: str | None
    currency: str
    current_value: float
    invested_amount: float
    gain: float
    return_pct: float
    tax_estimate: float
    quantity: float | None
    purchase_price: float | None
    is_active: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def compute_gain(cls, values):
        if hasattr(values, "__dict__"):
            current = getattr(values, "current_value", 0.0) or 0.0
            invested = getattr(values, "invested_amount", 0.0) or 0.0
        else:
            current = values.get("current_value", 0.0) or 0.0
            invested = values.get("invested_amount", 0.0) or 0.0
        gain = current - invested
        return_pct = (gain / invested * 100) if invested else 0.0
        # Tax estimate: Abgeltungssteuer on gains above 1000€ allowance
        taxable = max(0.0, gain - 1000.0)
        tax_est = round(taxable * 0.26375, 2)
        if hasattr(values, "__dict__"):
            values.__dict__["gain"] = gain
            values.__dict__["return_pct"] = return_pct
            values.__dict__["tax_estimate"] = tax_est
        else:
            values["gain"] = gain
            values["return_pct"] = return_pct
            values["tax_estimate"] = tax_est
        return values
