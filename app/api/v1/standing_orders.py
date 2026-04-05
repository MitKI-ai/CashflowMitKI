from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.user import User
from app.schemas.standing_order import StandingOrderCreate, StandingOrderResponse, StandingOrderUpdate
from app.services.standing_order_service import StandingOrderService

router = APIRouter(prefix="/standing-orders", tags=["standing-orders"])


@router.get("/", response_model=list[StandingOrderResponse])
def list_standing_orders(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return StandingOrderService.list(db, tenant_id=tenant_id)


@router.get("/{order_id}", response_model=StandingOrderResponse)
def get_standing_order(
    order_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    order = StandingOrderService.get(db, order_id=order_id, tenant_id=tenant_id)
    if not order:
        raise HTTPException(status_code=404, detail="Standing order not found")
    return order


@router.post("/", response_model=StandingOrderResponse, status_code=201)
def create_standing_order(
    data: StandingOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return StandingOrderService.create(
        db, tenant_id=tenant_id, user_id=current_user.id, **data.model_dump()
    )


@router.put("/{order_id}", response_model=StandingOrderResponse)
def update_standing_order(
    order_id: str,
    data: StandingOrderUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    order = StandingOrderService.get(db, order_id=order_id, tenant_id=tenant_id)
    if not order:
        raise HTTPException(status_code=404, detail="Standing order not found")
    return StandingOrderService.update(db, order=order, **data.model_dump(exclude_unset=True))


@router.delete("/{order_id}")
def delete_standing_order(
    order_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    order = StandingOrderService.get(db, order_id=order_id, tenant_id=tenant_id)
    if not order:
        raise HTTPException(status_code=404, detail="Standing order not found")
    StandingOrderService.delete(db, order=order)
    return {"message": "Standing order deleted"}
