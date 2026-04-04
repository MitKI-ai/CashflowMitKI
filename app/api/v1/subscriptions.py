from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/", response_model=list[SubscriptionResponse])
def list_subscriptions(
    status: str | None = None,
    billing_cycle: str | None = None,
    category_id: str | None = None,
    sort_by: str = "name",
    sort_dir: str = "asc",
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return SubscriptionService.list(
        db,
        tenant_id=tenant_id,
        status=status,
        billing_cycle=billing_cycle,
        category_id=category_id,
        sort_by=sort_by,
        sort_dir=sort_dir,
        skip=skip,
        limit=limit,
    )


@router.get("/{sub_id}", response_model=SubscriptionResponse)
def get_subscription(
    sub_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    sub = SubscriptionService.get(db, sub_id=sub_id, tenant_id=tenant_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.post("/", response_model=SubscriptionResponse, status_code=201)
def create_subscription(
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return SubscriptionService.create(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        name=data.name,
        provider=data.provider,
        cost=data.cost,
        currency=data.currency,
        billing_cycle=data.billing_cycle,
        status=data.status,
        start_date=data.start_date,
        next_renewal=data.next_renewal,
        auto_renew=data.auto_renew,
        notify_days_before=data.notify_days_before,
        notes=data.notes,
        icon_id=data.icon_id,
        plan_id=data.plan_id,
        category_ids=data.category_ids,
        custom_fields=data.custom_fields or {},
    )


@router.put("/{sub_id}", response_model=SubscriptionResponse)
def update_subscription(
    sub_id: str,
    data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    sub = SubscriptionService.get(db, sub_id=sub_id, tenant_id=tenant_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return SubscriptionService.update(db, sub=sub, **data.model_dump(exclude_unset=True))


@router.delete("/{sub_id}")
def delete_subscription(
    sub_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    sub = SubscriptionService.get(db, sub_id=sub_id, tenant_id=tenant_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    SubscriptionService.delete(db, sub=sub)
    return {"message": "Subscription deleted"}
