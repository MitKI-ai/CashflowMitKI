"""Tests for Investment CRUD API — STORY-060."""
import pytest


def test_list_investments_empty(auth_client):
    r = auth_client.get("/api/v1/investments/")
    assert r.status_code == 200
    assert r.json() == []


def test_create_investment(auth_client):
    r = auth_client.post("/api/v1/investments/", json={
        "name": "World ETF MSCI",
        "type": "etf",
        "account_id": None,
        "current_value": 10000.0,
        "invested_amount": 8000.0,
        "currency": "EUR",
        "broker": "Trade Republic",
        "isin": "IE00B4L5Y983",
        "quantity": 45.5,
        "purchase_price": 175.82,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "World ETF MSCI"
    assert data["type"] == "etf"
    assert data["current_value"] == 10000.0
    assert data["invested_amount"] == 8000.0
    assert data["isin"] == "IE00B4L5Y983"
    assert "id" in data


def test_investment_gain_and_return(auth_client):
    r = auth_client.post("/api/v1/investments/", json={
        "name": "Bitcoin",
        "type": "crypto",
        "current_value": 5000.0,
        "invested_amount": 3000.0,
        "currency": "EUR",
    })
    assert r.status_code == 201
    data = r.json()
    # gain = current_value - invested_amount
    assert data["gain"] == pytest.approx(2000.0)
    # return_pct = (gain / invested_amount) * 100
    assert data["return_pct"] == pytest.approx(66.67, rel=1e-2)


def test_investment_types(auth_client):
    for inv_type in ["etf", "stock", "crypto", "bond", "real_estate", "other"]:
        r = auth_client.post("/api/v1/investments/", json={
            "name": f"Test {inv_type}",
            "type": inv_type,
            "current_value": 1000.0,
            "invested_amount": 1000.0,
        })
        assert r.status_code == 201, f"Failed for type {inv_type}"


def test_list_investments_shows_all(auth_client):
    auth_client.post("/api/v1/investments/", json={"name": "A", "type": "etf", "current_value": 1000.0, "invested_amount": 800.0})
    auth_client.post("/api/v1/investments/", json={"name": "B", "type": "stock", "current_value": 500.0, "invested_amount": 400.0})
    r = auth_client.get("/api/v1/investments/")
    assert r.status_code == 200
    names = [i["name"] for i in r.json()]
    assert "A" in names
    assert "B" in names


def test_get_investment_by_id(auth_client):
    create = auth_client.post("/api/v1/investments/", json={
        "name": "NASDAQ ETF",
        "type": "etf",
        "current_value": 2000.0,
        "invested_amount": 1800.0,
    })
    inv_id = create.json()["id"]
    r = auth_client.get(f"/api/v1/investments/{inv_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "NASDAQ ETF"


def test_update_investment(auth_client):
    create = auth_client.post("/api/v1/investments/", json={
        "name": "Old Name",
        "type": "etf",
        "current_value": 1000.0,
        "invested_amount": 900.0,
    })
    inv_id = create.json()["id"]
    r = auth_client.put(f"/api/v1/investments/{inv_id}", json={"current_value": 1200.0})
    assert r.status_code == 200
    assert r.json()["current_value"] == 1200.0


def test_delete_investment(auth_client):
    create = auth_client.post("/api/v1/investments/", json={
        "name": "To Delete",
        "type": "other",
        "current_value": 100.0,
        "invested_amount": 100.0,
    })
    inv_id = create.json()["id"]
    r = auth_client.delete(f"/api/v1/investments/{inv_id}")
    assert r.status_code == 200
    r2 = auth_client.get(f"/api/v1/investments/{inv_id}")
    assert r2.status_code == 404


def test_investment_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/investments/", json={"name": "Tenant1 ETF", "type": "etf", "current_value": 5000.0, "invested_amount": 4000.0})
    r = auth_client_b.get("/api/v1/investments/")
    names = [i["name"] for i in r.json()]
    assert "Tenant1 ETF" not in names


def test_investment_portfolio_total_header(auth_client):
    auth_client.post("/api/v1/investments/", json={"name": "X", "type": "etf", "current_value": 3000.0, "invested_amount": 2500.0})
    auth_client.post("/api/v1/investments/", json={"name": "Y", "type": "crypto", "current_value": 1500.0, "invested_amount": 1000.0})
    r = auth_client.get("/api/v1/investments/")
    assert r.status_code == 200
    assert "x-portfolio-value" in r.headers
    assert float(r.headers["x-portfolio-value"]) == pytest.approx(4500.0)
