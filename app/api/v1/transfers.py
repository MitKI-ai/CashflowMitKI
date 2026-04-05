from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.transfer import Transfer
from app.models.user import User
from app.schemas.transfer import TransferCreate, TransferResponse

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.get("/", response_model=list[TransferResponse])
def list_transfers(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return (
        db.query(Transfer)
        .filter(Transfer.tenant_id == tenant_id)
        .order_by(Transfer.transfer_date.desc())
        .all()
    )


@router.post("/", response_model=TransferResponse, status_code=201)
def create_transfer(
    data: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    if data.from_account_id == data.to_account_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")
    transfer = Transfer(tenant_id=tenant_id, created_by_id=current_user.id, **data.model_dump())
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


@router.delete("/{transfer_id}")
def delete_transfer(
    transfer_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id, Transfer.tenant_id == tenant_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    db.delete(transfer)
    db.commit()
    return {"message": "Transfer deleted"}
