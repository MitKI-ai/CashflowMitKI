from sqlalchemy.orm import Session

from app.models.direct_debit import DirectDebit


class DirectDebitService:
    @staticmethod
    def list(db: Session, *, tenant_id: str) -> list[DirectDebit]:
        return (
            db.query(DirectDebit)
            .filter(DirectDebit.tenant_id == tenant_id, DirectDebit.is_active == True)
            .order_by(DirectDebit.name)
            .all()
        )

    @staticmethod
    def get(db: Session, *, debit_id: str, tenant_id: str) -> DirectDebit | None:
        return (
            db.query(DirectDebit)
            .filter(DirectDebit.id == debit_id, DirectDebit.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def create(db: Session, *, tenant_id: str, user_id: str, **kwargs) -> DirectDebit:
        debit = DirectDebit(tenant_id=tenant_id, created_by_id=user_id, **kwargs)
        db.add(debit)
        db.commit()
        db.refresh(debit)
        return debit

    @staticmethod
    def update(db: Session, *, debit: DirectDebit, **kwargs) -> DirectDebit:
        for key, value in kwargs.items():
            if hasattr(debit, key):
                setattr(debit, key, value)
        db.commit()
        db.refresh(debit)
        return debit

    @staticmethod
    def delete(db: Session, *, debit: DirectDebit) -> None:
        db.delete(debit)
        db.commit()
