"""Tests for Budget Alerts — STORY-078."""
import pytest


def test_list_budget_alerts_empty(auth_client):
    r = auth_client.get("/api/v1/budget-alerts/")
    assert r.status_code == 200
    assert r.json() == []


def test_create_budget_alert(auth_client):
    r = auth_client.post("/api/v1/budget-alerts/", json={
        "name": "Lebensmittel",
        "category": "food",
        "monthly_limit": 400.0,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Lebensmittel"
    assert data["monthly_limit"] == 400.0
    assert data["is_active"] is True


def test_budget_alert_check_under_limit(auth_client):
    """When spending is under limit, alert shows ok."""
    auth_client.post("/api/v1/budget-alerts/", json={
        "name": "Transport",
        "category": "transport",
        "monthly_limit": 200.0,
    })
    # Add a small transaction
    auth_client.post("/api/v1/transactions/", json={
        "description": "Bus ticket",
        "amount": 50.0,
        "type": "expense",
        "category": "transport",
        "transaction_date": "2026-03-15",
    })
    r = auth_client.get("/api/v1/budget-alerts/status?month=2026-03")
    assert r.status_code == 200
    data = r.json()
    transport = [a for a in data if a["category"] == "transport"]
    assert len(transport) == 1
    assert transport[0]["spent"] == pytest.approx(50.0)
    assert transport[0]["remaining"] == pytest.approx(150.0)
    assert transport[0]["exceeded"] is False


def test_budget_alert_check_over_limit(auth_client):
    """When spending exceeds limit, alert is triggered."""
    auth_client.post("/api/v1/budget-alerts/", json={
        "name": "Essen gehen",
        "category": "dining",
        "monthly_limit": 100.0,
    })
    auth_client.post("/api/v1/transactions/", json={
        "description": "Restaurant 1", "amount": 60.0, "type": "expense",
        "category": "dining", "transaction_date": "2026-03-10",
    })
    auth_client.post("/api/v1/transactions/", json={
        "description": "Restaurant 2", "amount": 55.0, "type": "expense",
        "category": "dining", "transaction_date": "2026-03-20",
    })
    r = auth_client.get("/api/v1/budget-alerts/status?month=2026-03")
    dining = [a for a in r.json() if a["category"] == "dining"]
    assert len(dining) == 1
    assert dining[0]["spent"] == pytest.approx(115.0)
    assert dining[0]["exceeded"] is True
    assert dining[0]["remaining"] == pytest.approx(-15.0)


def test_update_budget_alert(auth_client):
    create = auth_client.post("/api/v1/budget-alerts/", json={
        "name": "Test", "category": "test", "monthly_limit": 100.0,
    })
    alert_id = create.json()["id"]
    r = auth_client.put(f"/api/v1/budget-alerts/{alert_id}", json={"monthly_limit": 200.0})
    assert r.status_code == 200
    assert r.json()["monthly_limit"] == 200.0


def test_delete_budget_alert(auth_client):
    create = auth_client.post("/api/v1/budget-alerts/", json={
        "name": "Delete me", "category": "del", "monthly_limit": 50.0,
    })
    alert_id = create.json()["id"]
    r = auth_client.delete(f"/api/v1/budget-alerts/{alert_id}")
    assert r.status_code == 200


def test_budget_alert_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/budget-alerts/", json={
        "name": "Private Alert", "category": "secret", "monthly_limit": 500.0,
    })
    r = auth_client_b.get("/api/v1/budget-alerts/")
    names = [a["name"] for a in r.json()]
    assert "Private Alert" not in names
