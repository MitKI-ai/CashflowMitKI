from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.budget_alert import BudgetAlert
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget_alert import BudgetAlertCreate, BudgetAlertResponse, BudgetAlertStatus, BudgetAlertUpdate

router = APIRouter(prefix="/budget-alerts", tags=["budget-alerts"])


@router.get("/", response_model=list[BudgetAlertResponse])
def list_budget_alerts(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return (
        db.query(BudgetAlert)
        .filter(BudgetAlert.tenant_id == tenant_id, BudgetAlert.is_active == True)
        .order_by(BudgetAlert.name)
        .all()
    )


@router.post("/", response_model=BudgetAlertResponse, status_code=201)
def create_budget_alert(
    data: BudgetAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    alert = BudgetAlert(tenant_id=tenant_id, created_by_id=current_user.id, **data.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.put("/{alert_id}", response_model=BudgetAlertResponse)
def update_budget_alert(
    alert_id: str,
    data: BudgetAlertUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    alert = db.query(BudgetAlert).filter(
        BudgetAlert.id == alert_id, BudgetAlert.tenant_id == tenant_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Budget alert not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(alert, field, value)
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/{alert_id}")
def delete_budget_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    alert = db.query(BudgetAlert).filter(
        BudgetAlert.id == alert_id, BudgetAlert.tenant_id == tenant_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Budget alert not found")
    db.delete(alert)
    db.commit()
    return {"message": "Budget alert deleted"}


@router.get("/status", response_model=list[BudgetAlertStatus])
def budget_alert_status(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    alerts = (
        db.query(BudgetAlert)
        .filter(BudgetAlert.tenant_id == tenant_id, BudgetAlert.is_active == True)
        .all()
    )

    year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    date_from = f"{year}-{mon:02d}-01"
    date_to = f"{year}-{mon+1:02d}-01" if mon < 12 else f"{year+1}-01-01"

    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.tenant_id == tenant_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date < date_to,
        )
        .all()
    )

    # Group spending by category
    spending: dict[str, float] = {}
    for tx in transactions:
        spending[tx.category] = spending.get(tx.category, 0.0) + tx.amount

    result = []
    for alert in alerts:
        spent = spending.get(alert.category, 0.0)
        remaining = alert.monthly_limit - spent
        result.append(BudgetAlertStatus(
            id=alert.id,
            name=alert.name,
            category=alert.category,
            monthly_limit=alert.monthly_limit,
            spent=round(spent, 2),
            remaining=round(remaining, 2),
            exceeded=spent > alert.monthly_limit,
            pct_used=round(spent / alert.monthly_limit * 100, 1) if alert.monthly_limit else 0.0,
        ))

    return result
