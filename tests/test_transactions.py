"""Tests for Transaction CRUD API — STORY-061 (Haushaltsbuch)."""
from datetime import date


def test_list_transactions_empty(auth_client):
    r = auth_client.get("/api/v1/transactions/")
    assert r.status_code == 200
    assert r.json() == []


def test_create_expense_transaction(auth_client):
    r = auth_client.post("/api/v1/transactions/", json={
        "description": "Supermarkt Rewe",
        "amount": 85.50,
        "type": "expense",
        "category": "food",
        "transaction_date": "2026-03-15",
        "currency": "EUR",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["description"] == "Supermarkt Rewe"
    assert data["amount"] == 85.50
    assert data["type"] == "expense"
    assert data["category"] == "food"
    assert "id" in data


def test_create_income_transaction(auth_client):
    r = auth_client.post("/api/v1/transactions/", json={
        "description": "Freelance Projekt",
        "amount": 1200.0,
        "type": "income",
        "category": "income",
        "transaction_date": "2026-03-20",
    })
    assert r.status_code == 201
    assert r.json()["type"] == "income"


def test_transaction_types(auth_client):
    for tx_type in ["income", "expense", "transfer"]:
        r = auth_client.post("/api/v1/transactions/", json={
            "description": f"Test {tx_type}",
            "amount": 10.0,
            "type": tx_type,
            "transaction_date": "2026-03-01",
        })
        assert r.status_code == 201, f"Failed for type {tx_type}"


def test_list_transactions_filter_by_type(auth_client):
    auth_client.post("/api/v1/transactions/", json={"description": "Salary", "amount": 3000.0, "type": "income", "transaction_date": "2026-03-27"})
    auth_client.post("/api/v1/transactions/", json={"description": "Groceries", "amount": 50.0, "type": "expense", "transaction_date": "2026-03-10"})
    r = auth_client.get("/api/v1/transactions/?type=income")
    assert r.status_code == 200
    assert all(t["type"] == "income" for t in r.json())


def test_list_transactions_filter_by_month(auth_client):
    auth_client.post("/api/v1/transactions/", json={"description": "Feb item", "amount": 10.0, "type": "expense", "transaction_date": "2026-02-15"})
    auth_client.post("/api/v1/transactions/", json={"description": "Mar item", "amount": 20.0, "type": "expense", "transaction_date": "2026-03-15"})
    r = auth_client.get("/api/v1/transactions/?month=2026-03")
    assert r.status_code == 200
    descs = [t["description"] for t in r.json()]
    assert "Mar item" in descs
    assert "Feb item" not in descs


def test_update_transaction(auth_client):
    create = auth_client.post("/api/v1/transactions/", json={
        "description": "Old desc",
        "amount": 50.0,
        "type": "expense",
        "transaction_date": "2026-03-01",
    })
    tx_id = create.json()["id"]
    r = auth_client.put(f"/api/v1/transactions/{tx_id}", json={"description": "Updated desc", "amount": 75.0})
    assert r.status_code == 200
    assert r.json()["description"] == "Updated desc"
    assert r.json()["amount"] == 75.0


def test_delete_transaction(auth_client):
    create = auth_client.post("/api/v1/transactions/", json={
        "description": "To delete",
        "amount": 5.0,
        "type": "expense",
        "transaction_date": "2026-03-01",
    })
    tx_id = create.json()["id"]
    r = auth_client.delete(f"/api/v1/transactions/{tx_id}")
    assert r.status_code == 200
    r2 = auth_client.get(f"/api/v1/transactions/{tx_id}")
    assert r2.status_code == 404


def test_transaction_monthly_summary_header(auth_client):
    auth_client.post("/api/v1/transactions/", json={"description": "Income", "amount": 500.0, "type": "income", "transaction_date": "2026-03-01"})
    auth_client.post("/api/v1/transactions/", json={"description": "Expense", "amount": 200.0, "type": "expense", "transaction_date": "2026-03-05"})
    r = auth_client.get("/api/v1/transactions/?month=2026-03")
    assert "x-month-income" in r.headers
    assert "x-month-expense" in r.headers
    assert float(r.headers["x-month-income"]) == 500.0
    assert float(r.headers["x-month-expense"]) == 200.0


def test_transaction_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/transactions/", json={"description": "Private item", "amount": 100.0, "type": "expense", "transaction_date": "2026-03-01"})
    r = auth_client_b.get("/api/v1/transactions/")
    descs = [t["description"] for t in r.json()]
    assert "Private item" not in descs
