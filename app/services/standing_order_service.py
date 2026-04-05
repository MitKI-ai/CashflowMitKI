from sqlalchemy.orm import Session

from app.models.standing_order import StandingOrder


class StandingOrderService:
    @staticmethod
    def list(db: Session, *, tenant_id: str) -> list[StandingOrder]:
        return (
            db.query(StandingOrder)
            .filter(StandingOrder.tenant_id == tenant_id, StandingOrder.is_active == True)
            .order_by(StandingOrder.type, StandingOrder.name)
            .all()
        )

    @staticmethod
    def get(db: Session, *, order_id: str, tenant_id: str) -> StandingOrder | None:
        return (
            db.query(StandingOrder)
            .filter(StandingOrder.id == order_id, StandingOrder.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def create(db: Session, *, tenant_id: str, user_id: str, **kwargs) -> StandingOrder:
        order = StandingOrder(tenant_id=tenant_id, created_by_id=user_id, **kwargs)
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def update(db: Session, *, order: StandingOrder, **kwargs) -> StandingOrder:
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def delete(db: Session, *, order: StandingOrder) -> None:
        db.delete(order)
        db.commit()
