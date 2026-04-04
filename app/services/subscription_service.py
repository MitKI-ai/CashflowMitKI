"""SubscriptionService — thin DB wrapper keeping routes free of query logic."""
from __future__ import annotations

import json
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.subscription import Subscription
from app.services.audit_service import AuditService


class SubscriptionService:

    @staticmethod
    def list(
        db: Session,
        tenant_id: str,
        status: str | None = None,
        billing_cycle: str | None = None,
        category_id: str | None = None,
        sort_by: str = "name",
        sort_dir: str = "asc",
        skip: int = 0,
        limit: int = 50,
    ) -> list[Subscription]:
        q = db.query(Subscription).filter(Subscription.tenant_id == tenant_id)
        if status:
            q = q.filter(Subscription.status == status)
        if billing_cycle:
            q = q.filter(Subscription.billing_cycle == billing_cycle)
        if category_id:
            q = q.filter(Subscription.categories.any(Category.id == category_id))
        col = getattr(Subscription, sort_by, Subscription.name)
        q = q.order_by(col.asc() if sort_dir == "asc" else col.desc())
        return q.offset(skip).limit(limit).all()

    @staticmethod
    def get(db: Session, sub_id: str, tenant_id: str) -> Subscription | None:
        return (
            db.query(Subscription)
            .filter(Subscription.id == sub_id, Subscription.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        tenant_id: str,
        user_id: str,
        name: str,
        provider: str = "",
        cost: float = 0.0,
        currency: str = "EUR",
        billing_cycle: str = "monthly",
        status: str = "active",
        start_date: date | None = None,
        next_renewal: date | None = None,
        auto_renew: bool = False,
        notify_days_before: int = 7,
        notes: str | None = None,
        icon_id: str | None = None,
        plan_id: str | None = None,
        category_ids: list[str] | None = None,
        custom_fields: dict | None = None,
    ) -> Subscription:
        sub = Subscription(
            tenant_id=tenant_id,
            created_by_id=user_id,
            name=name,
            provider=provider,
            cost=cost,
            currency=currency,
            billing_cycle=billing_cycle,
            status=status,
            start_date=start_date or date.today(),
            next_renewal=next_renewal,
            auto_renew=auto_renew,
            notify_days_before=notify_days_before,
            notes=notes,
            icon_id=icon_id,
            plan_id=plan_id,
            custom_fields_json=json.dumps(custom_fields) if custom_fields else None,
        )
        if category_ids:
            sub.categories = db.query(Category).filter(
                Category.id.in_(category_ids), Category.tenant_id == tenant_id
            ).all()
        db.add(sub)
        db.commit()
        db.refresh(sub)
        AuditService.log(
            db, tenant_id=tenant_id, user_id=user_id,
            action="create", entity_type="subscription", entity_id=sub.id,
            new_values={"name": sub.name, "cost": sub.cost},
        )
        return sub

    @staticmethod
    def update(db: Session, sub: Subscription, **kwargs: Any) -> Subscription:
        tenant_id = sub.tenant_id
        if "category_ids" in kwargs:
            cat_ids = kwargs.pop("category_ids")
            sub.categories = db.query(Category).filter(
                Category.id.in_(cat_ids), Category.tenant_id == tenant_id
            ).all()
        if "custom_fields" in kwargs:
            cf = kwargs.pop("custom_fields")
            sub.custom_fields_json = json.dumps(cf) if cf is not None else None
        for key, value in kwargs.items():
            setattr(sub, key, value)
        db.commit()
        db.refresh(sub)
        AuditService.log(
            db, tenant_id=tenant_id, user_id=None,
            action="update", entity_type="subscription", entity_id=sub.id,
        )
        return sub

    @staticmethod
    def delete(db: Session, sub: Subscription) -> None:
        AuditService.log(
            db, tenant_id=sub.tenant_id, user_id=None,
            action="delete", entity_type="subscription", entity_id=sub.id,
            old_values={"name": sub.name},
        )
        db.delete(sub)
        db.commit()
