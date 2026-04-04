from pydantic import BaseModel


class PlanCreate(BaseModel):
    name: str
    description: str | None = None
    price: float = 0.0
    currency: str = "EUR"
    billing_cycle: str = "monthly"
    features_json: str | None = None


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    billing_cycle: str | None = None
    features_json: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class PlanResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None
    price: float
    currency: str
    billing_cycle: str
    features_json: str | None
    is_active: bool
    sort_order: int

    model_config = {"from_attributes": True}
