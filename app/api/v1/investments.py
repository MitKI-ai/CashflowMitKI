from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.investment import Investment
from app.models.user import User
from app.schemas.investment import InvestmentCreate, InvestmentResponse, InvestmentUpdate

router = APIRouter(prefix="/investments", tags=["investments"])


@router.get("/", response_model=list[InvestmentResponse])
def list_investments(
    response: Response,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    investments = (
        db.query(Investment)
        .filter(Investment.tenant_id == tenant_id, Investment.is_active == True)
        .order_by(Investment.created_at.desc())
        .all()
    )
    total = sum(i.current_value for i in investments)
    response.headers["X-Portfolio-Value"] = str(total)
    return investments


@router.post("/", response_model=InvestmentResponse, status_code=201)
def create_investment(
    data: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    investment = Investment(tenant_id=tenant_id, created_by_id=current_user.id, **data.model_dump())
    db.add(investment)
    db.commit()
    db.refresh(investment)
    return investment


@router.get("/{investment_id}", response_model=InvestmentResponse)
def get_investment(
    investment_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    investment = db.query(Investment).filter(
        Investment.id == investment_id, Investment.tenant_id == tenant_id
    ).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    return investment


@router.put("/{investment_id}", response_model=InvestmentResponse)
def update_investment(
    investment_id: str,
    data: InvestmentUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    investment = db.query(Investment).filter(
        Investment.id == investment_id, Investment.tenant_id == tenant_id
    ).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(investment, field, value)
    db.commit()
    db.refresh(investment)
    return investment


@router.delete("/{investment_id}")
def delete_investment(
    investment_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    investment = db.query(Investment).filter(
        Investment.id == investment_id, Investment.tenant_id == tenant_id
    ).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    db.delete(investment)
    db.commit()
    return {"message": "Investment deleted"}
