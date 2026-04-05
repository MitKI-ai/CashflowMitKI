import json
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, model_validator


class SubscriptionCreate(BaseModel):
    name: str
    provider: str = ""
    cost: float = 0.0
    currency: str = "EUR"
    billing_cycle: str = "monthly"
    status: str = "active"
    start_date: date | None = None
    next_renewal: date | None = None
    auto_renew: bool = True
    notify_days_before: int = 7
    notes: str | None = None
    icon_id: str | None = None
    plan_id: str | None = None
    category_ids: list[str] = []
    custom_fields: dict[str, Any] = {}


class SubscriptionUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    cost: float | None = None
    currency: str | None = None
    billing_cycle: str | None = None
    status: str | None = None
    next_renewal: date | None = None
    end_date: date | None = None
    auto_renew: bool | None = None
    notify_days_before: int | None = None
    notes: str | None = None
    icon_id: str | None = None
    plan_id: str | None = None
    category_ids: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


class SubscriptionResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    provider: str
    cost: float
    currency: str
    billing_cycle: str
    status: str
    start_date: date
    next_renewal: date | None
    end_date: date | None
    auto_renew: bool
    notify_days_before: int
    notes: str | None
    icon_id: str | None
    plan_id: str | None
    created_at: datetime
    custom_fields: dict[str, Any] = {}

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_custom_fields(cls, values):
        if hasattr(values, "__dict__"):
            raw = getattr(values, "custom_fields_json", None)
            if raw:
                try:
                    values.__dict__["custom_fields"] = json.loads(raw)
                except (ValueError, TypeError):
                    values.__dict__["custom_fields"] = {}
            else:
                values.__dict__["custom_fields"] = {}
        elif isinstance(values, dict):
            raw = values.get("custom_fields_json")
            if raw and "custom_fields" not in values:
                try:
                    values["custom_fields"] = json.loads(raw)
                except (ValueError, TypeError):
                    values["custom_fields"] = {}
        return values
