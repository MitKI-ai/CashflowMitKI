"""Custom Fields API — STORY-039"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, require_role
from app.models.custom_field import CustomField
from app.models.user import User

router = APIRouter(prefix="/custom-fields", tags=["custom-fields"])


class CustomFieldCreate(BaseModel):
    name: str
    field_type: str = "text"
    required: bool = False


class CustomFieldResponse(BaseModel):
    id: str
    name: str
    field_type: str
    required: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/", status_code=201, response_model=CustomFieldResponse)
def create_custom_field(
    body: CustomFieldCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    cf = CustomField(
        tenant_id=tenant_id,
        name=body.name,
        field_type=body.field_type,
        required=body.required,
    )
    db.add(cf)
    db.commit()
    db.refresh(cf)
    return cf


@router.get("/", response_model=list[CustomFieldResponse])
def list_custom_fields(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return db.query(CustomField).filter(CustomField.tenant_id == tenant_id).all()


@router.delete("/{field_id}")
def delete_custom_field(
    field_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    cf = db.query(CustomField).filter(
        CustomField.id == field_id, CustomField.tenant_id == tenant_id
    ).first()
    if not cf:
        raise HTTPException(status_code=404, detail="Custom field not found")
    db.delete(cf)
    db.commit()
    return {"ok": True}
