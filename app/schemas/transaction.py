from datetime import date, datetime

from pydantic import BaseModel


class TransactionCreate(BaseModel):
    description: str
    amount: float
    type: str  # income, expense, transfer
    category: str = ""
    currency: str = "EUR"
    transaction_date: date
    account_id: str | None = None
    is_recurring: bool = False
    notes: str | None = None


class TransactionUpdate(BaseModel):
    description: str | None = None
    amount: float | None = None
    type: str | None = None
    category: str | None = None
    currency: str | None = None
    transaction_date: date | None = None
    account_id: str | None = None
    is_recurring: bool | None = None
    notes: str | None = None


class TransactionResponse(BaseModel):
    id: str
    tenant_id: str
    account_id: str | None
    description: str
    amount: float
    type: str
    category: str
    currency: str
    transaction_date: date
    is_recurring: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
