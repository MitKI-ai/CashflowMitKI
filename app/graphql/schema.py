"""GraphQL Schema — STORY-045

Strawberry schema exposing Subscriptions and Plans.
Auth: reads Bearer token or session cookie via FastAPI dependency.
"""
from __future__ import annotations

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from app.database import get_db
from app.dependencies import get_current_user
from app.models.plan import Plan as PlanModel
from app.models.subscription import Subscription as SubscriptionModel

# ── GraphQL Types ──────────────────────────────────────────────────────────────

@strawberry.type
class SubscriptionType:
    id: str
    name: str
    provider: str
    cost: float
    currency: str
    billing_cycle: str
    status: str
    auto_renew: bool
    notes: str | None
    icon_id: str | None


@strawberry.type
class PlanType:
    id: str
    name: str
    price: float
    billing_cycle: str
    is_active: bool


# ── Context helper ─────────────────────────────────────────────────────────────

def _get_user_and_db(info: Info):
    """Extract current user + db session from Strawberry request context."""
    request = info.context["request"]
    db = next(get_db())
    user = get_current_user(request, db)
    return user, db


# ── Query ──────────────────────────────────────────────────────────────────────

@strawberry.type
class Query:

    @strawberry.field
    def subscriptions(self, info: Info) -> list[SubscriptionType]:
        user, db = _get_user_and_db(info)
        rows = db.query(SubscriptionModel).filter(
            SubscriptionModel.tenant_id == user.tenant_id
        ).all()
        return [
            SubscriptionType(
                id=s.id, name=s.name, provider=s.provider, cost=s.cost,
                currency=s.currency, billing_cycle=s.billing_cycle,
                status=s.status, auto_renew=s.auto_renew,
                notes=s.notes, icon_id=s.icon_id,
            )
            for s in rows
        ]

    @strawberry.field
    def subscription(self, info: Info, id: str) -> SubscriptionType | None:
        user, db = _get_user_and_db(info)
        s = db.query(SubscriptionModel).filter(
            SubscriptionModel.id == id,
            SubscriptionModel.tenant_id == user.tenant_id,
        ).first()
        if not s:
            return None
        return SubscriptionType(
            id=s.id, name=s.name, provider=s.provider, cost=s.cost,
            currency=s.currency, billing_cycle=s.billing_cycle,
            status=s.status, auto_renew=s.auto_renew,
            notes=s.notes, icon_id=s.icon_id,
        )

    @strawberry.field
    def plans(self, info: Info) -> list[PlanType]:
        user, db = _get_user_and_db(info)
        rows = db.query(PlanModel).filter(PlanModel.tenant_id == user.tenant_id).all()
        return [
            PlanType(
                id=p.id, name=p.name, price=p.price,
                billing_cycle=p.billing_cycle, is_active=p.is_active,
            )
            for p in rows
        ]


# ── Mutation ───────────────────────────────────────────────────────────────────

@strawberry.type
class Mutation:

    @strawberry.mutation
    def create_subscription(
        self,
        info: Info,
        name: str,
        cost: float,
        billing_cycle: str,
        provider: str = "",
        currency: str = "EUR",
        notes: str | None = None,
    ) -> SubscriptionType:
        from datetime import date
        user, db = _get_user_and_db(info)
        sub = SubscriptionModel(
            tenant_id=user.tenant_id,
            created_by_id=user.id,
            name=name,
            provider=provider,
            cost=cost,
            currency=currency,
            billing_cycle=billing_cycle,
            notes=notes,
            start_date=date.today(),
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return SubscriptionType(
            id=sub.id, name=sub.name, provider=sub.provider, cost=sub.cost,
            currency=sub.currency, billing_cycle=sub.billing_cycle,
            status=sub.status, auto_renew=sub.auto_renew,
            notes=sub.notes, icon_id=sub.icon_id,
        )

    @strawberry.mutation
    def delete_subscription(self, info: Info, id: str) -> bool:
        user, db = _get_user_and_db(info)
        sub = db.query(SubscriptionModel).filter(
            SubscriptionModel.id == id,
            SubscriptionModel.tenant_id == user.tenant_id,
        ).first()
        if not sub:
            return False
        db.delete(sub)
        db.commit()
        return True


# ── Router ─────────────────────────────────────────────────────────────────────

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema, graphql_ide="graphiql")
