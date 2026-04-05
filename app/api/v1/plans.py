from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, require_role
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=list[PlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return db.query(Plan).filter(Plan.tenant_id == tenant_id).order_by(Plan.sort_order).all()


@router.post("/", response_model=PlanResponse, status_code=201)
def create_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _admin=Depends(require_role(["admin"])),
):
    plan = Plan(tenant_id=tenant_id, **data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: str,
    data: PlanUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _admin=Depends(require_role(["admin"])),
):
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.tenant_id == tenant_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _admin=Depends(require_role(["admin"])),
):
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.tenant_id == tenant_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"message": "Plan deleted"}
