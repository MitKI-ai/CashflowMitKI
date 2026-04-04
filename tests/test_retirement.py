"""Tests for Retirement Profile + Calculator — STORY-064."""
import pytest


# ── Retirement Profile CRUD ──────────────────────────────────────────

def test_get_retirement_profile_default(auth_client):
    """New users get a default empty profile."""
    r = auth_client.get("/api/v1/retirement/profile")
    assert r.status_code == 200
    data = r.json()
    assert data["current_age"] == 0
    assert data["retirement_age"] == 67


def test_update_retirement_profile(auth_client):
    r = auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 38,
        "retirement_age": 65,
        "desired_monthly_income": 2500.0,
        "expected_pension": 1200.0,
        "life_expectancy": 85,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["current_age"] == 38
    assert data["retirement_age"] == 65
    assert data["desired_monthly_income"] == 2500.0
    assert data["expected_pension"] == 1200.0
    assert data["life_expectancy"] == 85


def test_retirement_profile_persists(auth_client):
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 40,
        "retirement_age": 67,
        "desired_monthly_income": 3000.0,
    })
    r = auth_client.get("/api/v1/retirement/profile")
    assert r.json()["current_age"] == 40
    assert r.json()["desired_monthly_income"] == 3000.0


def test_retirement_profile_tenant_isolation(auth_client, auth_client_b):
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 50,
        "retirement_age": 65,
    })
    r = auth_client_b.get("/api/v1/retirement/profile")
    assert r.json()["current_age"] == 0  # default, not tenant A's data


# ── Retirement Calculator ────────────────────────────────────────────

def test_retirement_calculate_basic(auth_client):
    """Calculate retirement gap and required savings."""
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 38,
        "retirement_age": 65,
        "desired_monthly_income": 2500.0,
        "expected_pension": 1200.0,
        "life_expectancy": 85,
    })
    r = auth_client.get("/api/v1/retirement/calculate")
    assert r.status_code == 200
    data = r.json()
    assert "monthly_gap" in data
    assert "years_to_retirement" in data
    assert "total_needed" in data
    assert "monthly_savings_required" in data
    assert data["monthly_gap"] == pytest.approx(1300.0)
    assert data["years_to_retirement"] == 27
    assert data["retirement_years"] == 20


def test_retirement_calculate_with_existing_savings(auth_client):
    """Existing savings reduce the required monthly contribution."""
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 38,
        "retirement_age": 65,
        "desired_monthly_income": 2500.0,
        "expected_pension": 1200.0,
        "life_expectancy": 85,
        "current_savings": 50000.0,
        "expected_return_pct": 3.0,
    })
    r = auth_client.get("/api/v1/retirement/calculate")
    data = r.json()
    assert data["monthly_gap"] == pytest.approx(1300.0)
    assert data["current_savings"] == pytest.approx(50000.0)
    assert data["monthly_savings_required"] > 0
    assert data["total_needed"] > 0
    # 50k at 3% over 27 years = ~111k, total needed = 312k, so gap remains
    assert data["future_value_savings"] < data["total_needed"]


def test_retirement_calculate_no_gap(auth_client):
    """When pension covers desired income, gap is zero."""
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 60,
        "retirement_age": 65,
        "desired_monthly_income": 1000.0,
        "expected_pension": 1500.0,
        "life_expectancy": 85,
    })
    r = auth_client.get("/api/v1/retirement/calculate")
    data = r.json()
    assert data["monthly_gap"] == 0.0
    assert data["monthly_savings_required"] == 0.0


def test_retirement_calculate_zero_return(auth_client):
    """With 0% return, calculation still works (no division by zero)."""
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 30,
        "retirement_age": 67,
        "desired_monthly_income": 2000.0,
        "expected_pension": 800.0,
        "life_expectancy": 85,
        "expected_return_pct": 0.0,
    })
    r = auth_client.get("/api/v1/retirement/calculate")
    assert r.status_code == 200
    data = r.json()
    assert data["monthly_savings_required"] > 0
