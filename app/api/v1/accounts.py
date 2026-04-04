from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=list[AccountResponse])
def list_accounts(
    response: Response,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    accounts = AccountService.list(db, tenant_id=tenant_id)
    total = AccountService.total_balance(db, tenant_id=tenant_id)
    response.headers["X-Total-Balance"] = str(total)
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    account = AccountService.get(db, account_id=account_id, tenant_id=tenant_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/", response_model=AccountResponse, status_code=201)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return AccountService.create(
        db, tenant_id=tenant_id, user_id=current_user.id, **data.model_dump()
    )


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: str,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    account = AccountService.get(db, account_id=account_id, tenant_id=tenant_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountService.update(db, account=account, **data.model_dump(exclude_unset=True))


@router.delete("/{account_id}")
def delete_account(
    account_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    account = AccountService.get(db, account_id=account_id, tenant_id=tenant_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    AccountService.delete(db, account=account)
    return {"message": "Account deleted"}
