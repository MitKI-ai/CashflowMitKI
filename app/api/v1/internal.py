"""Internal API endpoints — called by Prefect flows (STORY-025)

Protected by X-Internal-Key header (shared secret, not user-facing).
"""
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.account import Account
from app.models.investment import Investment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.cashflow import CashflowService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


def _require_internal_key(x_internal_key: str | None = Header(None, alias="X-Internal-Key")):
    if not x_internal_key or x_internal_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid internal API key")


# ── POST /internal/renewal-reminders ─────────────────────────────────────────

@router.post("/renewal-reminders")
def trigger_renewal_reminders(
    days_ahead: int = 7,
    db: Session = Depends(get_db),
    _: None = Depends(_require_internal_key),
):
    """Find active subscriptions renewing within `days_ahead` days and send reminder emails."""
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    subs = (
        db.query(Subscription)
        .filter(
            Subscription.status == "active",
            Subscription.next_renewal != None,  # noqa: E711
            Subscription.next_renewal >= today,
            Subscription.next_renewal <= cutoff,
        )
        .all()
    )

    sent = 0
    for sub in subs:
        # Find admin/owner of this tenant to email
        user = (
            db.query(User)
            .filter(User.tenant_id == sub.tenant_id, User.role == "admin", User.is_active == True)  # noqa: E712
            .first()
        )
        if not user:
            continue
        days_until = (sub.next_renewal - today).days
        ok = EmailService.send_renewal_reminder(sub, user.email, days_until=days_until)
        if ok:
            sent += 1
        else:
            logger.warning("Failed to send renewal reminder for subscription %s", sub.id)

    logger.info("Renewal reminders: sent=%d, total_due=%d", sent, len(subs))
    return {"sent": sent, "total_due": len(subs)}


# ── POST /internal/process-renewals ──────────────────────────────────────────

@router.post("/process-renewals")
def process_renewals(
    db: Session = Depends(get_db),
    _: None = Depends(_require_internal_key),
):
    """
    - Subscriptions with end_date < today and auto_renew=False → set status=expired
    - Subscriptions with next_renewal <= today and auto_renew=True → advance next_renewal
    """
    today = date.today()
    renewed = 0
    expired = 0

    # Expire overdue subscriptions
    overdue = (
        db.query(Subscription)
        .filter(
            Subscription.status == "active",
            Subscription.end_date != None,  # noqa: E711
            Subscription.end_date < today,
            Subscription.auto_renew == False,  # noqa: E712
        )
        .all()
    )
    for sub in overdue:
        sub.status = "expired"
        db.add(sub)
        user = (
            db.query(User)
            .filter(User.tenant_id == sub.tenant_id, User.role == "admin", User.is_active == True)  # noqa: E712
            .first()
        )
        if user:
            EmailService.send_expiry_notice(sub, user.email)
        expired += 1

    # Auto-renew: advance next_renewal date
    due_for_renewal = (
        db.query(Subscription)
        .filter(
            Subscription.status == "active",
            Subscription.next_renewal != None,  # noqa: E711
            Subscription.next_renewal <= today,
            Subscription.auto_renew == True,  # noqa: E712
        )
        .all()
    )
    _cycle_days = {"weekly": 7, "monthly": 30, "quarterly": 91, "yearly": 365}
    for sub in due_for_renewal:
        delta = timedelta(days=_cycle_days.get(sub.billing_cycle, 30))
        sub.next_renewal = sub.next_renewal + delta
        db.add(sub)
        renewed += 1

    db.commit()
    logger.info("process-renewals: renewed=%d, expired=%d", renewed, expired)
    return {"renewed": renewed, "expired": expired}


# ── POST /internal/send-cashflow-reports ────────────────────────────────────

@router.post("/send-cashflow-reports")
def send_cashflow_reports(
    db: Session = Depends(get_db),
    _: None = Depends(_require_internal_key),
):
    """Send monthly cashflow reports to all active admin users."""
    import calendar
    today = date.today()
    # Report for previous month
    if today.month == 1:
        report_month = f"{today.year - 1}-12"
        month_name = calendar.month_name[12]
    else:
        report_month = f"{today.year}-{today.month - 1:02d}"
        month_name = calendar.month_name[today.month - 1]

    month_label = f"{month_name} {report_month.split('-')[0]}"

    admins = db.query(User).filter(User.role == "admin", User.is_active == True).all()

    sent = 0
    for admin in admins:
        summary = CashflowService.monthly_summary(db, tenant_id=admin.tenant_id)
        accounts_sum = sum(
            a.balance for a in db.query(Account).filter(
                Account.tenant_id == admin.tenant_id, Account.is_active == True
            ).all()
        )
        investments_sum = sum(
            i.current_value for i in db.query(Investment).filter(
                Investment.tenant_id == admin.tenant_id, Investment.is_active == True
            ).all()
        )
        net_worth = accounts_sum + investments_sum

        ok = EmailService.send_cashflow_report(
            to=admin.email,
            user_name=admin.display_name or admin.email,
            month=month_label,
            summary=summary,
            net_worth=net_worth,
        )
        if ok:
            sent += 1

    logger.info("cashflow-reports: sent=%d, admins=%d", sent, len(admins))
    return {"sent": sent, "total_admins": len(admins)}


# ── POST /internal/bookings/generate ─────────────────────────────────────────

@router.post("/bookings/generate")
def internal_generate_bookings(
    year: int,
    month: int,
    auto_confirm: bool = True,
    db: Session = Depends(get_db),
    _: None = Depends(_require_internal_key),
):
    """Generate (and optionally confirm) bookings for all active tenants."""
    from app.models.tenant import Tenant
    from app.services.booking_service import BookingService

    tenants = db.query(Tenant).all()
    total_generated = 0
    total_confirmed = 0

    for tenant in tenants:
        # Use first admin user of the tenant as created_by
        admin = db.query(User).filter(
            User.tenant_id == tenant.id,
            User.role == "admin",
            User.is_active == True,
        ).first()
        if not admin:
            continue

        pending = BookingService.generate_pending(
            db, tenant_id=tenant.id, year=year, month=month
        )
        total_generated += len(pending)

        if auto_confirm and pending:
            created = BookingService.confirm_bookings(
                db, tenant_id=tenant.id, user_id=admin.id, bookings=pending
            )
            total_confirmed += len(created)

    logger.info(
        "internal bookings generate: year=%d month=%d tenants=%d generated=%d confirmed=%d",
        year, month, len(tenants), total_generated, total_confirmed,
    )
    return {
        "year": year, "month": month,
        "tenants_processed": len(tenants),
        "generated": total_generated,
        "confirmed": total_confirmed if auto_confirm else 0,
    }


# ── POST /internal/reports/send-all ──────────────────────────────────────────

@router.post("/reports/send-all")
def internal_send_reports(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    _: None = Depends(_require_internal_key),
):
    """Send PDF cashflow reports to all active admin users for the given month."""
    import calendar as cal_mod

    from app.services.report_service import ReportService

    month_label = f"{month:02d}/{year}"
    admins = db.query(User).filter(User.role == "admin", User.is_active == True).all()

    sent = 0
    for admin in admins:
        summary = CashflowService.monthly_summary(db, tenant_id=admin.tenant_id)
        investments = db.query(Investment).filter(Investment.tenant_id == admin.tenant_id).all()
        net_worth = sum(i.current_value for i in investments)

        ok = EmailService.send_cashflow_report(
            to=admin.email,
            user_name=admin.display_name or admin.email,
            month=month_label,
            summary=summary,
            net_worth=net_worth,
        )
        if ok:
            sent += 1

    logger.info("internal reports/send-all: year=%d month=%d sent=%d", year, month, sent)
    return {"year": year, "month": month, "sent": sent, "total_admins": len(admins)}
