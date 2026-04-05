"""Tests for Admin Analytics Dashboard MRR+Churn — STORY-036"""
from datetime import date, timedelta
from tests.conftest import make_subscription


def test_analytics_page_accessible_by_admin(auth_client):
    r = auth_client.get("/analytics")
    assert r.status_code == 200


def test_analytics_page_blocked_for_non_admin(user_client):
    r = user_client.get("/analytics", follow_redirects=False)
    assert r.status_code == 302


def test_analytics_api_returns_mrr(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, cost=10.0, billing_cycle="monthly", status="active")
    make_subscription(db, tenant_a.id, admin_user.id, cost=120.0, billing_cycle="yearly", status="active")
    r = auth_client.get("/api/v1/analytics/summary")
    assert r.status_code == 200
    data = r.json()
    assert "mrr" in data
    # 10 monthly + 120/12 yearly = 10 + 10 = 20
    assert abs(data["mrr"] - 20.0) < 0.01


def test_analytics_api_returns_arr(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, cost=10.0, billing_cycle="monthly", status="active")
    r = auth_client.get("/api/v1/analytics/summary")
    data = r.json()
    assert "arr" in data
    assert abs(data["arr"] - 120.0) < 0.01


def test_analytics_api_returns_churn(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, cost=10.0, status="active")
    make_subscription(db, tenant_a.id, admin_user.id, cost=10.0, status="cancelled")
    r = auth_client.get("/api/v1/analytics/summary")
    data = r.json()
    assert "churn_rate" in data
    assert 0 <= data["churn_rate"] <= 100


def test_analytics_api_returns_active_count(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, status="active")
    make_subscription(db, tenant_a.id, admin_user.id, status="active")
    make_subscription(db, tenant_a.id, admin_user.id, status="cancelled")
    r = auth_client.get("/api/v1/analytics/summary")
    data = r.json()
    assert data["active_count"] == 2
    assert data["total_count"] == 3


def test_analytics_tenant_isolated(auth_client, auth_client_b, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, cost=99.0, billing_cycle="monthly", status="active")
    r = auth_client_b.get("/api/v1/analytics/summary")
    assert r.json()["mrr"] == 0.0


def test_analytics_mrr_history(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, cost=10.0, billing_cycle="monthly", status="active")
    r = auth_client.get("/api/v1/analytics/mrr-history?months=3")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 3
    for entry in data:
        assert "month" in entry
        assert "mrr" in entry
