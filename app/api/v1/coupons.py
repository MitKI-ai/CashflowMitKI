"""Coupons API — STORY-038"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user, require_role
from app.models.coupon import Coupon
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(prefix="/coupons", tags=["coupons"])


class CouponCreate(BaseModel):
    code: str
    discount_type: str = "percent"
    discount_value: float
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None


class CouponResponse(BaseModel):
    id: str
    code: str
    discount_type: str
    discount_value: float
    max_uses: Optional[int]
    uses_count: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplyCoupon(BaseModel):
    code: str
    subscription_id: str


@router.post("/", status_code=201, response_model=CouponResponse)
def create_coupon(
    body: CouponCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    existing = db.query(Coupon).filter(
        Coupon.tenant_id == tenant_id, Coupon.code == body.code.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Coupon code already exists")

    c = Coupon(
        tenant_id=tenant_id,
        code=body.code.upper(),
        discount_type=body.discount_type,
        discount_value=body.discount_value,
        max_uses=body.max_uses,
        expires_at=body.expires_at,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/", response_model=list[CouponResponse])
def list_coupons(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return db.query(Coupon).filter(Coupon.tenant_id == tenant_id).all()


@router.delete("/{coupon_id}")
def delete_coupon(
    coupon_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    c = db.query(Coupon).filter(Coupon.id == coupon_id, Coupon.tenant_id == tenant_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Coupon not found")
    db.delete(c)
    db.commit()
    return {"ok": True}


@router.get("/validate")
def validate_coupon(
    code: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    c = db.query(Coupon).filter(
        Coupon.tenant_id == tenant_id,
        Coupon.code == code.upper(),
        Coupon.is_active == True,  # noqa: E712
    ).first()
    if not c:
        return {"valid": False}
    now = datetime.now(timezone.utc)
    if c.expires_at and c.expires_at.replace(tzinfo=timezone.utc) < now:
        return {"valid": False, "reason": "expired"}
    if c.max_uses and c.uses_count >= c.max_uses:
        return {"valid": False, "reason": "max_uses_reached"}
    return {
        "valid": True,
        "discount_type": c.discount_type,
        "discount_value": c.discount_value,
    }


@router.post("/apply")
def apply_coupon(
    body: ApplyCoupon,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    c = db.query(Coupon).filter(
        Coupon.tenant_id == tenant_id,
        Coupon.code == body.code.upper(),
        Coupon.is_active == True,  # noqa: E712
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Coupon not found or inactive")

    now = datetime.now(timezone.utc)
    if c.expires_at and c.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=410, detail="Coupon expired")

    sub = db.query(Subscription).filter(
        Subscription.id == body.subscription_id,
        Subscription.tenant_id == tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if c.discount_type == "percent":
        new_cost = round(sub.cost * (1 - c.discount_value / 100), 2)
    else:
        new_cost = round(max(sub.cost - c.discount_value, 0), 2)

    sub.cost = new_cost
    c.uses_count += 1
    db.commit()
    return {"new_cost": new_cost, "coupon_code": c.code, "discount_applied": c.discount_value}
