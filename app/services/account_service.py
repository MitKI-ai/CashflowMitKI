from sqlalchemy.orm import Session

from app.models.account import Account


class AccountService:
    @staticmethod
    def list(db: Session, *, tenant_id: str) -> list[Account]:
        return (
            db.query(Account)
            .filter(Account.tenant_id == tenant_id, Account.is_active == True)
            .order_by(Account.name)
            .all()
        )

    @staticmethod
    def get(db: Session, *, account_id: str, tenant_id: str) -> Account | None:
        return (
            db.query(Account)
            .filter(Account.id == account_id, Account.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def total_balance(db: Session, *, tenant_id: str) -> float:
        from sqlalchemy import func
        result = (
            db.query(func.coalesce(func.sum(Account.balance), 0.0))
            .filter(Account.tenant_id == tenant_id, Account.is_active == True)
            .scalar()
        )
        return float(result)

    @staticmethod
    def create(db: Session, *, tenant_id: str, user_id: str, **kwargs) -> Account:
        iban = kwargs.pop("iban", None)
        account = Account(tenant_id=tenant_id, created_by_id=user_id, **kwargs)
        if iban:
            account.iban = iban
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def update(db: Session, *, account: Account, **kwargs) -> Account:
        for key, value in kwargs.items():
            if hasattr(account, key):
                setattr(account, key, value)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def delete(db: Session, *, account: Account) -> None:
        db.delete(account)
        db.commit()
