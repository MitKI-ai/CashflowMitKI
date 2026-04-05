"""Tests — PDF Finanzreport (EPIC-208 / Sprint 20)."""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.investment import Investment
from app.models.savings_goal import SavingsGoal
from app.models.standing_order import StandingOrder
from app.models.tenant import Tenant
from app.models.transaction import Transaction
from app.models.user import User
from app.services.report_service import ReportService

# ── Unit: ReportService ───────────────────────────────────────────────────────

def test_generate_pdf_returns_bytes():
    summary = {
        "monthly_income": 4500.0,
        "monthly_expenses": 1300.0,
        "monthly_direct_debits": 310.0,
        "monthly_subscriptions": 50.0,
        "monthly_savings": 500.0,
        "monthly_net": 2340.0,
    }
    pdf = ReportService.generate_monthly_pdf(
        tenant_name="Test GmbH",
        user_name="Test User",
        year=2026,
        month=3,
        cashflow_summary=summary,
        net_worth=40000.0,
        savings_goals=[
            {"name": "Notgroschen", "current": 8500.0, "target": 15000.0}
        ],
        top_transactions=[
            {"date": "05.03.", "description": "REWE Einkauf", "category": "food", "amount": 87.50, "type": "expense"}
        ],
    )
    assert isinstance(pdf, bytes)
    # PDF magic bytes
    assert pdf[:4] == b"%PDF"


def test_generate_pdf_minimal():
    """Works with empty optional fields."""
    summary = {
        "monthly_income": 1000.0,
        "monthly_expenses": 0.0,
        "monthly_direct_debits": 0.0,
        "monthly_subscriptions": 0.0,
        "monthly_savings": 0.0,
        "monthly_net": 1000.0,
    }
    pdf = ReportService.generate_monthly_pdf(
        tenant_name="Mini GmbH",
        user_name="Solo User",
        year=2026,
        month=1,
        cashflow_summary=summary,
    )
    assert pdf[:4] == b"%PDF"


def test_generate_pdf_negative_cashflow():
    """Handles negative net cashflow without error."""
    summary = {
        "monthly_income": 500.0,
        "monthly_expenses": 2000.0,
        "monthly_direct_debits": 200.0,
        "monthly_subscriptions": 100.0,
        "monthly_savings": 0.0,
        "monthly_net": -1800.0,
    }
    pdf = ReportService.generate_monthly_pdf(
        tenant_name="Broke GmbH",
        user_name="Broke User",
        year=2026,
        month=2,
        cashflow_summary=summary,
        net_worth=0.0,
    )
    assert pdf[:4] == b"%PDF"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def seeded(db: Session, tenant_a: Tenant, admin_user: User):
    """Seed minimal cashflow data."""
    acc = Account(
        tenant_id=tenant_a.id, created_by_id=admin_user.id,
        name="Girokonto", type="checking", balance=3200.0,
    )
    db.add(acc)
    db.flush()  # get acc.id
    inv = Investment(
        tenant_id=tenant_a.id, created_by_id=admin_user.id,
        name="ETF", type="etf", broker="Trade Republic",
        current_value=10000.0, invested_amount=8000.0,
    )
    sg = SavingsGoal(
        tenant_id=tenant_a.id, created_by_id=admin_user.id,
        name="Notgroschen", type="emergency",
        target_amount=15000.0, current_amount=5000.0,
    )
    so = StandingOrder(
        tenant_id=tenant_a.id, created_by_id=admin_user.id,
        account_id=acc.id, name="Gehalt", type="income",
        amount=4500.0, frequency="monthly", execution_day=27,
    )
    tx = Transaction(
        tenant_id=tenant_a.id, created_by_id=admin_user.id,
        description="REWE", amount=87.50, type="expense",
        category="food", transaction_date=date(2026, 3, 5),
    )
    db.add_all([inv, sg, so, tx])
    db.commit()
    return {"account": acc, "investment": inv, "savings_goal": sg}


# ── API: Download PDF ─────────────────────────────────────────────────────────

def test_api_download_pdf(auth_client: TestClient, seeded):
    r = auth_client.get("/api/v1/reports/monthly/2026/3/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
    assert "cashflow-report-2026-03.pdf" in r.headers["content-disposition"]


def test_api_download_pdf_current_month(auth_client: TestClient, seeded):
    r = auth_client.get("/api/v1/reports/monthly/current/pdf")
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_api_pdf_requires_auth(client: TestClient):
    r = client.get("/api/v1/reports/monthly/2026/3/pdf")
    assert r.status_code in (401, 403)


# ── API: Send Email ───────────────────────────────────────────────────────────

def test_api_send_email_returns_200(auth_client: TestClient, seeded):
    """E-mail send is expected to fail (no SMTP in test) but endpoint must return 200."""
    r = auth_client.post("/api/v1/reports/monthly/2026/3/send-email")
    assert r.status_code == 200
    data = r.json()
    assert "sent" in data
    assert "to" in data


# ── Web page ──────────────────────────────────────────────────────────────────

def test_reports_page_renders(auth_client: TestClient, seeded):
    r = auth_client.get("/reports")
    assert r.status_code == 200
    assert "Finanzberichte" in r.text
    assert "PDF herunterladen" in r.text


# ── Internal endpoint ─────────────────────────────────────────────────────────

def test_internal_send_reports(client: TestClient, seeded, admin_user):
    r = client.post(
        "/api/v1/internal/reports/send-all",
        params={"year": 2026, "month": 3},
        headers={"X-Internal-Key": "test-internal-key"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["year"] == 2026
    assert data["month"] == 3
    assert "sent" in data
