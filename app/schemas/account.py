from datetime import datetime

from pydantic import BaseModel


class AccountCreate(BaseModel):
    name: str
    type: str = "checking"  # checking, savings, investment, deposit
    bank_name: str = ""
    iban: str | None = None
    balance: float = 0.0
    currency: str = "EUR"
    is_primary: bool = False
    interest_rate: float = 0.0
    notes: str | None = None


class AccountUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    bank_name: str | None = None
    iban: str | None = None
    balance: float | None = None
    currency: str | None = None
    is_primary: bool | None = None
    interest_rate: float | None = None
    is_active: bool | None = None
    notes: str | None = None


class AccountResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    type: str
    bank_name: str
    balance: float
    currency: str
    is_primary: bool
    interest_rate: float
    is_active: bool
    notes: str | None
    created_at: datetime
    # IBAN intentionally excluded — never expose in API responses

    model_config = {"from_attributes": True}
