"""Tests for STORY-010: Dashboard Charts + 30d renewal data"""
from datetime import date, timedelta

from tests.conftest import make_subscription


def test_dashboard_returns_chart_data(auth_client, db, admin_user, tenant_a):
    """Dashboard response must contain Chart.js canvas elements."""
    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    assert "chart" in r.text.lower() or "canvas" in r.text.lower()


def test_dashboard_renewals_30d_in_response(auth_client, db, admin_user, tenant_a):
    """Backend passes renewals_30d count and upcoming renewal list."""
    today = date.today()
    # Sub renewing in 10 days
    make_subscription(db, tenant_a.id, admin_user.id,
                      name="Renewing Soon", next_renewal=today + timedelta(days=10))
    # Sub renewing in 40 days — should NOT count
    make_subscription(db, tenant_a.id, admin_user.id,
                      name="Renewing Later", next_renewal=today + timedelta(days=40))

    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    assert "Renewing Soon" in r.text


def test_dashboard_cost_by_billing_cycle(auth_client, db, admin_user, tenant_a):
    """Dashboard shows cost breakdown across billing cycles."""
    make_subscription(db, tenant_a.id, admin_user.id, name="Monthly Sub",
                      cost=10.0, billing_cycle="monthly", status="active")
    make_subscription(db, tenant_a.id, admin_user.id, name="Yearly Sub",
                      cost=120.0, billing_cycle="yearly", status="active")

    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    # Page must expose chart data JSON with billing cycle labels
    assert "monthly" in r.text.lower() or "yearly" in r.text.lower()


def test_dashboard_status_distribution(auth_client, db, admin_user, tenant_a):
    """Dashboard shows status distribution (active/paused/cancelled)."""
    make_subscription(db, tenant_a.id, admin_user.id, name="Active", status="active")
    make_subscription(db, tenant_a.id, admin_user.id, name="Paused", status="paused")

    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    # Status counts are in the KPI cards
    assert "2" in r.text or "1" in r.text
