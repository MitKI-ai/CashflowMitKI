"""Webhook Endpoints API — STORY-037"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, require_role
from app.models.user import User
from app.models.webhook import WebhookEndpoint

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookCreate(BaseModel):
    url: str
    events: list[str] = ["*"]
    is_active: bool = True


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        data = {
            "id": obj.id,
            "url": obj.url,
            "events": json.loads(obj.events or '["*"]'),
            "is_active": obj.is_active,
            "created_at": obj.created_at,
        }
        return cls(**data)


@router.post("/", status_code=201)
def create_webhook(
    body: WebhookCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    wh = WebhookEndpoint(
        tenant_id=tenant_id,
        url=body.url,
        events=json.dumps(body.events),
        is_active=body.is_active,
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return WebhookResponse.from_orm(wh)


@router.get("/")
def list_webhooks(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    whs = db.query(WebhookEndpoint).filter(WebhookEndpoint.tenant_id == tenant_id).all()
    return [WebhookResponse.from_orm(w) for w in whs]


@router.delete("/{wh_id}")
def delete_webhook(
    wh_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    wh = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == wh_id, WebhookEndpoint.tenant_id == tenant_id
    ).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(wh)
    db.commit()
    return {"ok": True}
