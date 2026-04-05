from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.savings_goal import SavingsGoal
from app.models.user import User
from app.schemas.savings_goal import SavingsGoalCreate, SavingsGoalResponse, SavingsGoalUpdate

router = APIRouter(prefix="/savings-goals", tags=["savings-goals"])


@router.get("/", response_model=list[SavingsGoalResponse])
def list_savings_goals(
    response: Response,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    goals = (
        db.query(SavingsGoal)
        .filter(SavingsGoal.tenant_id == tenant_id, SavingsGoal.is_active == True)
        .order_by(SavingsGoal.created_at.asc())
        .all()
    )
    total_saved = sum(g.current_amount for g in goals)
    response.headers["X-Total-Saved"] = str(total_saved)
    return goals


@router.post("/", response_model=SavingsGoalResponse, status_code=201)
def create_savings_goal(
    data: SavingsGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    goal = SavingsGoal(tenant_id=tenant_id, created_by_id=current_user.id, **data.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/{goal_id}", response_model=SavingsGoalResponse)
def get_savings_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id, SavingsGoal.tenant_id == tenant_id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    return goal


@router.put("/{goal_id}", response_model=SavingsGoalResponse)
def update_savings_goal(
    goal_id: str,
    data: SavingsGoalUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id, SavingsGoal.tenant_id == tenant_id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}")
def delete_savings_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id, SavingsGoal.tenant_id == tenant_id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    db.delete(goal)
    db.commit()
    return {"message": "Savings goal deleted"}
