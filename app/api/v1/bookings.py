"""Auto-Buchungen API — EPIC-212 / STORY-103–106."""
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


class ConfirmRequest(BaseModel):
    bookings: list[dict[str, Any]]


# ── Preview ──────────────────────────────────────────────────────────────────

@router.get("/pending")
def pending_bookings(
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return pending bookings for the given month (defaults to current month)."""
    today = date.today()
    y = year or today.year
    m = month or today.month
    if not (1 <= m <= 12):
        raise HTTPException(status_code=400, detail="month must be 1–12")

    pending = BookingService.generate_pending(
        db, tenant_id=current_user.tenant_id, year=y, month=m
    )
    return {"year": y, "month": m, "count": len(pending), "bookings": pending}


# ── Confirm ───────────────────────────────────────────────────────────────────

@router.post("/confirm")
def confirm_bookings(
    payload: ConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create Transactions from the supplied booking list."""
    if not payload.bookings:
        raise HTTPException(status_code=400, detail="No bookings provided")

    created = BookingService.confirm_bookings(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        bookings=payload.bookings,
    )
    return {"created": len(created), "ids": [tx.id for tx in created]}


# ── Prefect trigger (internal) ────────────────────────────────────────────────

@router.post("/generate-for-month")
def generate_for_month(
    year: int,
    month: int,
    auto_confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate (and optionally auto-confirm) bookings for a specific month.
    Intended for use by Prefect monthly flow and admin UI.
    """
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="month must be 1–12")

    pending = BookingService.generate_pending(
        db, tenant_id=current_user.tenant_id, year=year, month=month
    )

    if auto_confirm and pending:
        created = BookingService.confirm_bookings(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            bookings=pending,
        )
        return {"year": year, "month": month, "generated": len(created), "auto_confirmed": True}

    return {"year": year, "month": month, "pending": len(pending), "auto_confirmed": False, "bookings": pending}
