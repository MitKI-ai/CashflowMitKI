from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Subscription, Tenant, User

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": settings.app_version,
        "environment": settings.app_env,
        "database": db_status,
    }


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    return {
        "tenants": db.query(Tenant).count(),
        "users": db.query(User).count(),
        "subscriptions_total": db.query(Subscription).count(),
        "subscriptions_active": db.query(Subscription).filter(Subscription.status == "active").count(),
    }
