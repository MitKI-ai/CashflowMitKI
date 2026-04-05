"""Search API — STORY-031"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.user import User
from app.services.search_service import init_fts, search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
def search_subscriptions(
    q: str = Query(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    # Ensure FTS is initialised (idempotent)
    init_fts(db)
    results = search(db, tenant_id, q)
    return [
        {
            "id": s.id,
            "name": s.name,
            "provider": s.provider,
            "cost": s.cost,
            "currency": s.currency,
            "billing_cycle": s.billing_cycle,
            "status": s.status,
        }
        for s in results
    ]
