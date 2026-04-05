"""Tests for CashflowService — STORY-065.

CashflowService aggregates all recurring income/expense streams into a
monthly cashflow summary:
  Cashflow = Σ StandingOrders(income)
           - Σ StandingOrders(expense)
           - Σ DirectDebits
           - Σ Subscriptions(active)
           - Σ StandingOrders(savings_transfer)
"""
import pytest

# ── Cashflow Summary API ─────────────────────────────────────────────

def test_cashflow_summary_empty(auth_client):
    """Empty tenant returns zero cashflow."""
    r = auth_client.get("/api/v1/cashflow/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["monthly_income"] == 0.0
    assert data["monthly_expenses"] == 0.0
    assert data["monthly_subscriptions"] == 0.0
    assert data["monthly_savings"] == 0.0
    assert data["monthly_net"] == 0.0


def test_cashflow_summary_with_standing_orders(auth_client):
    """Standing orders contribute to income and expenses."""
    # Create an account first
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Girokonto", "type": "checking", "bank_name": "Test",
    }).json()
    acc_id = acc["id"]

    # Income standing order
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Gehalt", "type": "income", "amount": 4500.0,
        "frequency": "monthly", "execution_day": 27, "account_id": acc_id,
    })
    # Expense standing order
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Miete", "type": "expense", "amount": 1200.0,
        "frequency": "monthly", "execution_day": 1, "account_id": acc_id,
    })
    # Savings transfer
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "ETF-Sparplan", "type": "savings_transfer", "amount": 500.0,
        "frequency": "monthly", "execution_day": 1, "account_id": acc_id,
    })

    r = auth_client.get("/api/v1/cashflow/summary")
    data = r.json()
    assert data["monthly_income"] == pytest.approx(4500.0)
    assert data["monthly_expenses"] == pytest.approx(1200.0)
    assert data["monthly_savings"] == pytest.approx(500.0)


def test_cashflow_summary_with_direct_debits(auth_client):
    """Direct debits are part of monthly expenses."""
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Konto", "type": "checking", "bank_name": "Test",
    }).json()
    acc_id = acc["id"]

    auth_client.post("/api/v1/direct-debits/", json={
        "name": "Strom", "amount": 85.0, "frequency": "monthly",
        "expected_day": 5, "account_id": acc_id,
    })
    auth_client.post("/api/v1/direct-debits/", json={
        "name": "GEZ", "amount": 55.08, "frequency": "quarterly",
        "expected_day": 15, "account_id": acc_id,
    })

    r = auth_client.get("/api/v1/cashflow/summary")
    data = r.json()
    # 85 + 55.08/3 = 85 + 18.36 = 103.36
    assert data["monthly_direct_debits"] == pytest.approx(103.36)


def test_cashflow_summary_with_subscriptions(auth_client):
    """Active subscriptions contribute to monthly expenses."""
    auth_client.post("/api/v1/subscriptions/", json={
        "name": "Netflix", "cost": 12.99, "billing_cycle": "monthly",
        "status": "active", "start_date": "2026-01-01",
    })
    auth_client.post("/api/v1/subscriptions/", json={
        "name": "Annual Service", "cost": 120.0, "billing_cycle": "yearly",
        "status": "active", "start_date": "2026-01-01",
    })

    r = auth_client.get("/api/v1/cashflow/summary")
    data = r.json()
    # 12.99 + 120/12 = 12.99 + 10 = 22.99
    assert data["monthly_subscriptions"] == pytest.approx(22.99)


def test_cashflow_net_calculation(auth_client):
    """Net = income - expenses - direct_debits - subscriptions - savings."""
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Girokonto", "type": "checking", "bank_name": "Test",
    }).json()
    acc_id = acc["id"]

    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Gehalt", "type": "income", "amount": 3000.0,
        "frequency": "monthly", "execution_day": 27, "account_id": acc_id,
    })
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Miete", "type": "expense", "amount": 1000.0,
        "frequency": "monthly", "execution_day": 1, "account_id": acc_id,
    })
    auth_client.post("/api/v1/direct-debits/", json={
        "name": "Internet", "amount": 50.0, "frequency": "monthly",
        "expected_day": 3, "account_id": acc_id,
    })
    auth_client.post("/api/v1/subscriptions/", json={
        "name": "Spotify", "cost": 10.0, "billing_cycle": "monthly",
        "status": "active", "start_date": "2026-01-01",
    })
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Sparplan", "type": "savings_transfer", "amount": 200.0,
        "frequency": "monthly", "execution_day": 1, "account_id": acc_id,
    })

    r = auth_client.get("/api/v1/cashflow/summary")
    data = r.json()
    expected_net = 3000.0 - 1000.0 - 50.0 - 10.0 - 200.0
    assert data["monthly_net"] == pytest.approx(expected_net)


def test_cashflow_summary_frequency_normalization(auth_client):
    """Yearly and quarterly amounts are normalized to monthly."""
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Konto", "type": "checking", "bank_name": "Test",
    }).json()
    acc_id = acc["id"]

    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Weihnachtsgeld", "type": "income", "amount": 1200.0,
        "frequency": "yearly", "execution_day": 15, "account_id": acc_id,
    })

    r = auth_client.get("/api/v1/cashflow/summary")
    data = r.json()
    assert data["monthly_income"] == pytest.approx(100.0)  # 1200/12


def test_cashflow_summary_tenant_isolation(auth_client, auth_client_b):
    """Tenant A data doesn't leak to tenant B."""
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Konto A", "type": "checking", "bank_name": "BankA",
    }).json()
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Gehalt A", "type": "income", "amount": 5000.0,
        "frequency": "monthly", "execution_day": 27, "account_id": acc["id"],
    })

    r = auth_client_b.get("/api/v1/cashflow/summary")
    data = r.json()
    assert data["monthly_income"] == 0.0
