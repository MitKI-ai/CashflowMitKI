"""Tests for 3-Scenario Retirement Calculator — STORY-081."""
import pytest


def test_scenarios_endpoint(auth_client):
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 38, "retirement_age": 65,
        "desired_monthly_income": 2500.0, "expected_pension": 1200.0,
        "life_expectancy": 85, "current_savings": 50000.0,
    })
    r = auth_client.get("/api/v1/retirement/scenarios")
    assert r.status_code == 200
    data = r.json()
    assert "pessimistic" in data
    assert "realistic" in data
    assert "optimistic" in data


def test_scenarios_different_returns(auth_client):
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 30, "retirement_age": 67,
        "desired_monthly_income": 2000.0, "expected_pension": 800.0,
        "life_expectancy": 85, "current_savings": 20000.0,
    })
    r = auth_client.get("/api/v1/retirement/scenarios")
    data = r.json()
    # Optimistic should need less monthly savings than pessimistic
    assert data["optimistic"]["monthly_savings_required"] < data["pessimistic"]["monthly_savings_required"]
    # Optimistic future value should be higher
    assert data["optimistic"]["future_value_savings"] > data["pessimistic"]["future_value_savings"]


def test_scenarios_custom_rates(auth_client):
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 40, "retirement_age": 65,
        "desired_monthly_income": 3000.0, "expected_pension": 1500.0,
        "life_expectancy": 85,
    })
    r = auth_client.get("/api/v1/retirement/scenarios?pessimistic=2&realistic=4&optimistic=8")
    assert r.status_code == 200
    data = r.json()
    assert data["pessimistic"]["return_pct"] == 2.0
    assert data["realistic"]["return_pct"] == 4.0
    assert data["optimistic"]["return_pct"] == 8.0


def test_scenarios_include_inflation(auth_client):
    auth_client.put("/api/v1/retirement/profile", json={
        "current_age": 35, "retirement_age": 67,
        "desired_monthly_income": 2500.0, "expected_pension": 1000.0,
        "life_expectancy": 85, "current_savings": 30000.0,
    })
    r = auth_client.get("/api/v1/retirement/scenarios?inflation=2.0")
    data = r.json()
    for scenario in ["pessimistic", "realistic", "optimistic"]:
        assert "real_total_needed" in data[scenario]
