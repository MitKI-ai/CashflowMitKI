"""Analytics API — STORY-036"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, require_role
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return AnalyticsService.summary(db, tenant_id)


@router.get("/mrr-history")
def mrr_history(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return AnalyticsService.mrr_history(db, tenant_id, months)
