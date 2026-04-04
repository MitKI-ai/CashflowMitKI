"""Tests for Capital Gains Tax Estimation — STORY-082."""
import pytest


def test_tax_estimation_endpoint(auth_client):
    r = auth_client.post("/api/v1/cashflow/tax-estimate", json={
        "capital_gains": 5000.0,
        "tax_free_allowance": 1000.0,
    })
    assert r.status_code == 200
    data = r.json()
    # Taxable: 5000 - 1000 = 4000
    # Tax: 4000 * 0.26375 = 1055
    assert data["taxable_gains"] == pytest.approx(4000.0)
    assert data["tax_amount"] == pytest.approx(1055.0)
    assert data["net_gains"] == pytest.approx(3945.0)
    assert data["effective_tax_rate"] == pytest.approx(21.1, rel=1e-1)


def test_tax_below_allowance(auth_client):
    r = auth_client.post("/api/v1/cashflow/tax-estimate", json={
        "capital_gains": 800.0,
        "tax_free_allowance": 1000.0,
    })
    data = r.json()
    assert data["taxable_gains"] == 0.0
    assert data["tax_amount"] == 0.0
    assert data["net_gains"] == 800.0


def test_tax_custom_rate(auth_client):
    r = auth_client.post("/api/v1/cashflow/tax-estimate", json={
        "capital_gains": 10000.0,
        "tax_free_allowance": 0.0,
        "tax_rate": 25.0,
    })
    data = r.json()
    assert data["tax_amount"] == pytest.approx(2500.0)


def test_investment_unrealized_gains_tax(auth_client):
    """Investment list includes tax estimate on unrealized gains."""
    auth_client.post("/api/v1/investments/", json={
        "name": "Tax Test ETF", "type": "etf",
        "current_value": 15000.0, "invested_amount": 10000.0,
    })
    r = auth_client.get("/api/v1/investments/")
    assert r.status_code == 200
    etf = [i for i in r.json() if i["name"] == "Tax Test ETF"][0]
    assert "tax_estimate" in etf
    # Gain = 5000, after 1000 allowance = 4000, tax = 4000 * 0.26375 ≈ 1055
    assert etf["tax_estimate"] >= 0
