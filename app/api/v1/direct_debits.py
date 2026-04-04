from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.user import User
from app.schemas.direct_debit import DirectDebitCreate, DirectDebitResponse, DirectDebitUpdate
from app.services.direct_debit_service import DirectDebitService

router = APIRouter(prefix="/direct-debits", tags=["direct-debits"])


@router.get("/", response_model=list[DirectDebitResponse])
def list_direct_debits(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return DirectDebitService.list(db, tenant_id=tenant_id)


@router.get("/{debit_id}", response_model=DirectDebitResponse)
def get_direct_debit(
    debit_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    debit = DirectDebitService.get(db, debit_id=debit_id, tenant_id=tenant_id)
    if not debit:
        raise HTTPException(status_code=404, detail="Direct debit not found")
    return debit


@router.post("/", response_model=DirectDebitResponse, status_code=201)
def create_direct_debit(
    data: DirectDebitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return DirectDebitService.create(
        db, tenant_id=tenant_id, user_id=current_user.id, **data.model_dump()
    )


@router.put("/{debit_id}", response_model=DirectDebitResponse)
def update_direct_debit(
    debit_id: str,
    data: DirectDebitUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    debit = DirectDebitService.get(db, debit_id=debit_id, tenant_id=tenant_id)
    if not debit:
        raise HTTPException(status_code=404, detail="Direct debit not found")
    return DirectDebitService.update(db, debit=debit, **data.model_dump(exclude_unset=True))


@router.delete("/{debit_id}")
def delete_direct_debit(
    debit_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    debit = DirectDebitService.get(db, debit_id=debit_id, tenant_id=tenant_id)
    if not debit:
        raise HTTPException(status_code=404, detail="Direct debit not found")
    DirectDebitService.delete(db, debit=debit)
    return {"message": "Direct debit deleted"}
