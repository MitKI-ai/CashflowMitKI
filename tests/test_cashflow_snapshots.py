"""Tests for Cashflow Snapshots — STORY-067."""
import pytest


def test_list_snapshots_empty(auth_client):
    r = auth_client.get("/api/v1/cashflow/snapshots")
    assert r.status_code == 200
    assert r.json() == []


def test_create_snapshot(auth_client):
    r = auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-03"})
    assert r.status_code == 201
    data = r.json()
    assert data["month"] == "2026-03"
    assert "monthly_income" in data
    assert "monthly_expenses" in data
    assert "monthly_net" in data
    assert "net_worth" in data
    assert "id" in data


def test_snapshot_captures_current_state(auth_client):
    """Snapshot values reflect the cashflow state at creation time."""
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Girokonto", "type": "checking", "bank_name": "Test", "balance": 5000.0,
    }).json()
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Gehalt", "type": "income", "amount": 3000.0,
        "frequency": "monthly", "execution_day": 27, "account_id": acc["id"],
    })

    r = auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-03"})
    data = r.json()
    assert data["monthly_income"] == pytest.approx(3000.0)
    assert data["net_worth"] >= 5000.0


def test_list_snapshots_returns_all(auth_client):
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-01"})
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-02"})
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-03"})
    r = auth_client.get("/api/v1/cashflow/snapshots")
    assert len(r.json()) >= 3
    months = [s["month"] for s in r.json()]
    assert "2026-01" in months
    assert "2026-02" in months
    assert "2026-03" in months


def test_snapshots_ordered_by_month(auth_client):
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-03"})
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-01"})
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-02"})
    r = auth_client.get("/api/v1/cashflow/snapshots")
    months = [s["month"] for s in r.json()]
    assert months == sorted(months)


def test_snapshot_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-03"})
    r = auth_client_b.get("/api/v1/cashflow/snapshots")
    assert r.json() == []


def test_trend_endpoint(auth_client):
    """Trend returns snapshots as data points for charting."""
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-01"})
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-02"})
    auth_client.post("/api/v1/cashflow/snapshots", json={"month": "2026-03"})
    r = auth_client.get("/api/v1/cashflow/trend")
    assert r.status_code == 200
    data = r.json()
    assert "months" in data
    assert "income" in data
    assert "expenses" in data
    assert "net" in data
    assert "net_worth" in data
    assert len(data["months"]) >= 3
