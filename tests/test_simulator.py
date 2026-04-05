"""Tests for What-If Simulator — STORY-077."""
import pytest


def test_simulate_endpoint(auth_client):
    """POST simulate returns adjusted cashflow."""
    r = auth_client.post("/api/v1/cashflow/simulate", json={
        "income_adjustment": 500.0,
        "expense_adjustment": -200.0,
        "savings_adjustment": 100.0,
    })
    assert r.status_code == 200
    data = r.json()
    assert "current" in data
    assert "scenario" in data
    assert "diff" in data


def test_simulate_income_increase(auth_client):
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Konto", "type": "checking", "bank_name": "Test",
    }).json()
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Gehalt", "type": "income", "amount": 3000.0,
        "frequency": "monthly", "execution_day": 27, "account_id": acc["id"],
    })

    r = auth_client.post("/api/v1/cashflow/simulate", json={
        "income_adjustment": 500.0,
        "expense_adjustment": 0.0,
        "savings_adjustment": 0.0,
    })
    data = r.json()
    assert data["scenario"]["monthly_income"] == pytest.approx(data["current"]["monthly_income"] + 500.0)
    assert data["diff"]["monthly_net"] == pytest.approx(500.0)


def test_simulate_expense_reduction(auth_client):
    r = auth_client.post("/api/v1/cashflow/simulate", json={
        "income_adjustment": 0.0,
        "expense_adjustment": -300.0,
        "savings_adjustment": 0.0,
    })
    data = r.json()
    # Reducing expenses should increase net
    assert data["diff"]["monthly_net"] == pytest.approx(300.0)


def test_simulate_savings_increase(auth_client):
    r = auth_client.post("/api/v1/cashflow/simulate", json={
        "income_adjustment": 0.0,
        "expense_adjustment": 0.0,
        "savings_adjustment": 200.0,
    })
    data = r.json()
    assert data["scenario"]["monthly_savings"] == pytest.approx(data["current"]["monthly_savings"] + 200.0)
    # Net decreases when savings increase
    assert data["diff"]["monthly_net"] == pytest.approx(-200.0)


def test_simulate_web_page_renders(auth_client):
    r = auth_client.get("/cashflow/simulator")
    assert r.status_code == 200
    assert "Simulator" in r.text or "simulator" in r.text.lower()


def test_simulate_no_changes(auth_client):
    r = auth_client.post("/api/v1/cashflow/simulate", json={
        "income_adjustment": 0.0,
        "expense_adjustment": 0.0,
        "savings_adjustment": 0.0,
    })
    data = r.json()
    assert data["diff"]["monthly_net"] == pytest.approx(0.0)
