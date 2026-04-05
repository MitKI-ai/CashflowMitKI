"""Tests for Inflation Parameter + Purchasing Power — STORY-080."""
import pytest


def test_purchasing_power_calculation(auth_client):
    """API calculates real value adjusted for inflation."""
    r = auth_client.post("/api/v1/cashflow/purchasing-power", json={
        "nominal_value": 100000.0,
        "years": 30,
        "inflation_rate": 2.0,
    })
    assert r.status_code == 200
    data = r.json()
    # 100000 / (1.02^30) ≈ 55207
    assert data["real_value"] == pytest.approx(55207.09, rel=1e-2)
    assert data["purchasing_power_loss_pct"] == pytest.approx(44.79, rel=1e-1)


def test_purchasing_power_zero_inflation(auth_client):
    r = auth_client.post("/api/v1/cashflow/purchasing-power", json={
        "nominal_value": 50000.0,
        "years": 10,
        "inflation_rate": 0.0,
    })
    data = r.json()
    assert data["real_value"] == pytest.approx(50000.0)
    assert data["purchasing_power_loss_pct"] == pytest.approx(0.0)


def test_purchasing_power_table(auth_client):
    """Returns year-by-year purchasing power erosion."""
    r = auth_client.post("/api/v1/cashflow/purchasing-power", json={
        "nominal_value": 100000.0,
        "years": 5,
        "inflation_rate": 3.0,
    })
    data = r.json()
    assert "yearly_breakdown" in data
    assert len(data["yearly_breakdown"]) == 5
    # Each year should have less real value
    for i in range(1, len(data["yearly_breakdown"])):
        assert data["yearly_breakdown"][i]["real_value"] < data["yearly_breakdown"][i - 1]["real_value"]


def test_retirement_with_inflation(auth_client):
    """Retirement calculation includes inflation-adjusted values."""
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 38,
        "retirement_age": 65,
        "desired_monthly_income": 2500.0,
        "expected_pension": 1200.0,
        "life_expectancy": 85,
        "expected_return_pct": 5.0,
    })
    r = auth_client.get("/api/v1/retirement/calculate?inflation=2.0")
    assert r.status_code == 200
    data = r.json()
    assert "real_total_needed" in data
    assert "real_monthly_gap" in data
    # Real values should be higher than nominal (need more to maintain purchasing power)
    assert data["real_total_needed"] >= data["total_needed"]


def test_default_inflation_rate(auth_client):
    """Default inflation rate is 2%."""
    r = auth_client.get("/api/v1/retirement/calculate")
    assert r.status_code == 200
    data = r.json()
    assert "real_total_needed" in data
