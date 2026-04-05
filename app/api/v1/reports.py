"""PDF Finanzreport API — EPIC-208 / Sprint 20."""
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.investment import Investment
from app.models.savings_goal import SavingsGoal
from app.models.tenant import Tenant
from app.models.transaction import Transaction
from app.models.user import User
from app.services.cashflow import CashflowService
from app.services.email_service import EmailService
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


def _build_report_data(
    db: Session,
    *,
    tenant_id: str,
    user: User,
    year: int,
    month: int,
) -> dict:
    cashflow_summary = CashflowService.monthly_summary(db, tenant_id=tenant_id)

    # Net worth = sum of account balances + investments
    investments = db.query(Investment).filter(Investment.tenant_id == tenant_id).all()
    net_worth = sum(inv.current_value for inv in investments)

    # Savings goals
    goals = db.query(SavingsGoal).filter(SavingsGoal.tenant_id == tenant_id).all()
    savings_goals_data = [
        {"name": g.name, "current": g.current_amount, "target": g.target_amount}
        for g in goals
    ]

    # Top 10 transactions for the month
    from calendar import monthrange
    last_day = monthrange(year, month)[1]
    txns = (
        db.query(Transaction)
        .filter(
            Transaction.tenant_id == tenant_id,
            Transaction.transaction_date >= date(year, month, 1),
            Transaction.transaction_date <= date(year, month, last_day),
        )
        .order_by(Transaction.transaction_date.desc())
        .limit(10)
        .all()
    )
    top_transactions = [
        {
            "date": t.transaction_date.strftime("%d.%m."),
            "description": t.description,
            "category": t.category,
            "amount": t.amount,
            "type": t.type,
        }
        for t in txns
    ]

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    tenant_name = tenant.name if tenant else ""

    return {
        "tenant_name": tenant_name,
        "user_name": user.display_name or user.email,
        "year": year,
        "month": month,
        "cashflow_summary": cashflow_summary,
        "net_worth": net_worth,
        "savings_goals": savings_goals_data,
        "top_transactions": top_transactions,
    }


# ── Download endpoint ──────────────────────────────────────────────────────────

@router.get("/monthly/{year}/{month}/pdf")
def download_monthly_report(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download PDF report for the given month."""
    data = _build_report_data(
        db, tenant_id=current_user.tenant_id, user=current_user, year=year, month=month
    )
    pdf_bytes = ReportService.generate_monthly_pdf(**data)
    filename = f"cashflow-report-{year}-{month:02d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── E-Mail send endpoint ───────────────────────────────────────────────────────

@router.post("/monthly/{year}/{month}/send-email")
def send_monthly_report_email(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send the monthly PDF report via e-mail to the current user."""
    data = _build_report_data(
        db, tenant_id=current_user.tenant_id, user=current_user, year=year, month=month
    )
    month_label = f"{month:02d}/{year}"
    ok = EmailService.send_cashflow_report(
        to=current_user.email,
        user_name=data["user_name"],
        month=month_label,
        summary=data["cashflow_summary"],
        net_worth=data["net_worth"],
    )
    return {"sent": ok, "to": current_user.email, "month": month_label}


# ── Latest / current-month shortcuts ──────────────────────────────────────────

@router.get("/monthly/current/pdf")
def download_current_month_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    return download_monthly_report(today.year, today.month, db=db, current_user=current_user)
