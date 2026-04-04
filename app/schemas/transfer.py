from datetime import date, datetime

from pydantic import BaseModel


class TransferCreate(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float
    currency: str = "EUR"
    description: str = ""
    transfer_date: date
    is_recurring: bool = False
    frequency: str | None = None
    savings_goal_id: str | None = None


class TransferResponse(BaseModel):
    id: str
    tenant_id: str
    from_account_id: str
    to_account_id: str
    amount: float
    currency: str
    description: str
    transfer_date: date
    is_recurring: bool
    frequency: str | None
    savings_goal_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
