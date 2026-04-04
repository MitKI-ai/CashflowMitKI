"""Tests for Savings Goals — STORY-063."""
import pytest


def test_list_savings_goals_empty(auth_client):
    r = auth_client.get("/api/v1/savings-goals/")
    assert r.status_code == 200
    assert r.json() == []


def test_create_emergency_fund(auth_client):
    r = auth_client.post("/api/v1/savings-goals/", json={
        "name": "Notgroschen",
        "type": "emergency",
        "target_amount": 10000.0,
        "current_amount": 3200.0,
        "currency": "EUR",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Notgroschen"
    assert data["type"] == "emergency"
    assert data["target_amount"] == 10000.0
    assert data["current_amount"] == 3200.0
    assert "id" in data


def test_create_vacation_goal(auth_client):
    r = auth_client.post("/api/v1/savings-goals/", json={
        "name": "Mallorca Sommer 2027",
        "type": "vacation_luxury",
        "target_amount": 3000.0,
        "current_amount": 500.0,
    })
    assert r.status_code == 201
    assert r.json()["type"] == "vacation_luxury"


def test_create_retirement_goal(auth_client):
    r = auth_client.post("/api/v1/savings-goals/", json={
        "name": "Rente mit 65",
        "type": "retirement",
        "target_amount": 500000.0,
        "current_amount": 28000.0,
    })
    assert r.status_code == 201
    assert r.json()["type"] == "retirement"


def test_progress_percentage(auth_client):
    r = auth_client.post("/api/v1/savings-goals/", json={
        "name": "Urlaub",
        "type": "vacation_luxury",
        "target_amount": 2000.0,
        "current_amount": 500.0,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["progress_pct"] == pytest.approx(25.0)


def test_progress_capped_at_100(auth_client):
    r = auth_client.post("/api/v1/savings-goals/", json={
        "name": "Overfunded",
        "type": "emergency",
        "target_amount": 1000.0,
        "current_amount": 1500.0,
    })
    assert r.status_code == 201
    assert r.json()["progress_pct"] == pytest.approx(100.0)


def test_update_savings_goal(auth_client):
    create = auth_client.post("/api/v1/savings-goals/", json={
        "name": "Test",
        "type": "emergency",
        "target_amount": 5000.0,
        "current_amount": 1000.0,
    })
    goal_id = create.json()["id"]
    r = auth_client.put(f"/api/v1/savings-goals/{goal_id}", json={"current_amount": 2000.0})
    assert r.status_code == 200
    assert r.json()["current_amount"] == 2000.0
    assert r.json()["progress_pct"] == pytest.approx(40.0)


def test_delete_savings_goal(auth_client):
    create = auth_client.post("/api/v1/savings-goals/", json={
        "name": "To delete",
        "type": "vacation_luxury",
        "target_amount": 500.0,
        "current_amount": 0.0,
    })
    goal_id = create.json()["id"]
    r = auth_client.delete(f"/api/v1/savings-goals/{goal_id}")
    assert r.status_code == 200
    r2 = auth_client.get(f"/api/v1/savings-goals/{goal_id}")
    assert r2.status_code == 404


def test_savings_goal_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/savings-goals/", json={"name": "Secret Goal", "type": "emergency", "target_amount": 5000.0, "current_amount": 0.0})
    r = auth_client_b.get("/api/v1/savings-goals/")
    names = [g["name"] for g in r.json()]
    assert "Secret Goal" not in names


def test_savings_goals_total_header(auth_client):
    auth_client.post("/api/v1/savings-goals/", json={"name": "G1", "type": "emergency", "target_amount": 5000.0, "current_amount": 1000.0})
    auth_client.post("/api/v1/savings-goals/", json={"name": "G2", "type": "vacation_luxury", "target_amount": 3000.0, "current_amount": 500.0})
    r = auth_client.get("/api/v1/savings-goals/")
    assert "x-total-saved" in r.headers
    assert float(r.headers["x-total-saved"]) == pytest.approx(1500.0)
