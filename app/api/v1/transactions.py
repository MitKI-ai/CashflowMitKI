from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=list[TransactionResponse])
def list_transactions(
    response: Response,
    type: str | None = Query(None),
    month: str | None = Query(None, description="Filter by month: YYYY-MM"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    q = db.query(Transaction).filter(Transaction.tenant_id == tenant_id)
    if type:
        q = q.filter(Transaction.type == type)
    if month:
        year, mon = int(month.split("-")[0]), int(month.split("-")[1])
        q = q.filter(
            Transaction.transaction_date >= f"{year}-{mon:02d}-01",
            Transaction.transaction_date < f"{year}-{mon+1:02d}-01" if mon < 12 else f"{year+1}-01-01",
        )
    transactions = q.order_by(Transaction.transaction_date.desc()).all()

    # Monthly summary headers
    if month:
        income = sum(t.amount for t in transactions if t.type == "income")
        expense = sum(t.amount for t in transactions if t.type == "expense")
        response.headers["X-Month-Income"] = str(income)
        response.headers["X-Month-Expense"] = str(expense)

    return transactions


@router.post("/", response_model=TransactionResponse, status_code=201)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    transaction = Transaction(tenant_id=tenant_id, created_by_id=current_user.id, **data.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id, Transaction.tenant_id == tenant_id
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id, Transaction.tenant_id == tenant_id
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id, Transaction.tenant_id == tenant_id
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(tx)
    db.commit()
    return {"message": "Transaction deleted"}
