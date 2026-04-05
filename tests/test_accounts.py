"""Tests for Account CRUD — STORY-054"""
from tests.conftest import make_category


def test_create_account(auth_client, tenant_a):
    r = auth_client.post("/api/v1/accounts", json={
        "name": "Girokonto Sparkasse",
        "type": "checking",
        "bank_name": "Sparkasse",
        "balance": 3200.00,
        "currency": "EUR",
        "is_primary": True,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Girokonto Sparkasse"
    assert data["type"] == "checking"
    assert data["bank_name"] == "Sparkasse"
    assert data["balance"] == 3200.00
    assert data["is_primary"] is True
    assert data["tenant_id"] == tenant_a.id
    assert "iban" not in data  # IBAN must never appear in response


def test_create_account_with_iban_excluded_from_response(auth_client):
    r = auth_client.post("/api/v1/accounts", json={
        "name": "Tagesgeld ING",
        "type": "savings",
        "bank_name": "ING",
        "balance": 12000.00,
        "iban": "DE89370400440532013000",
    })
    assert r.status_code == 201
    data = r.json()
    assert "iban" not in data
    assert data["name"] == "Tagesgeld ING"


def test_list_accounts(auth_client):
    auth_client.post("/api/v1/accounts", json={"name": "Girokonto", "type": "checking", "bank_name": "Sparkasse", "balance": 3200})
    auth_client.post("/api/v1/accounts", json={"name": "Sparkonto", "type": "savings", "bank_name": "ING", "balance": 12000})
    r = auth_client.get("/api/v1/accounts")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    # Check total_balance header
    assert "X-Total-Balance" in r.headers
    assert float(r.headers["X-Total-Balance"]) == 15200.00


def test_get_account(auth_client):
    create = auth_client.post("/api/v1/accounts", json={"name": "Depot", "type": "investment", "bank_name": "Trade Republic", "balance": 28000})
    acc_id = create.json()["id"]
    r = auth_client.get(f"/api/v1/accounts/{acc_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "Depot"


def test_update_account(auth_client):
    create = auth_client.post("/api/v1/accounts", json={"name": "Girokonto", "type": "checking", "bank_name": "Sparkasse", "balance": 3200})
    acc_id = create.json()["id"]
    r = auth_client.put(f"/api/v1/accounts/{acc_id}", json={"balance": 4500.50, "name": "Girokonto Haupt"})
    assert r.status_code == 200
    assert r.json()["balance"] == 4500.50
    assert r.json()["name"] == "Girokonto Haupt"


def test_delete_account(auth_client):
    create = auth_client.post("/api/v1/accounts", json={"name": "Testkonto", "type": "checking", "bank_name": "Test", "balance": 0})
    acc_id = create.json()["id"]
    r = auth_client.delete(f"/api/v1/accounts/{acc_id}")
    assert r.status_code == 200
    # Verify it's gone
    r2 = auth_client.get(f"/api/v1/accounts/{acc_id}")
    assert r2.status_code == 404


def test_tenant_isolation(auth_client, auth_client_b):
    """Tenant A cannot see Tenant B's accounts."""
    auth_client.post("/api/v1/accounts", json={"name": "Konto A", "type": "checking", "bank_name": "Bank A", "balance": 1000})
    auth_client_b.post("/api/v1/accounts", json={"name": "Konto B", "type": "checking", "bank_name": "Bank B", "balance": 2000})

    r_a = auth_client.get("/api/v1/accounts")
    r_b = auth_client_b.get("/api/v1/accounts")

    names_a = [a["name"] for a in r_a.json()]
    names_b = [a["name"] for a in r_b.json()]

    assert "Konto A" in names_a
    assert "Konto B" not in names_a
    assert "Konto B" in names_b
    assert "Konto A" not in names_b


def test_account_not_found(auth_client):
    r = auth_client.get("/api/v1/accounts/nonexistent-id")
    assert r.status_code == 404


def test_account_types(auth_client):
    """All 4 account types work."""
    for atype in ["checking", "savings", "investment", "deposit"]:
        r = auth_client.post("/api/v1/accounts", json={"name": f"Test {atype}", "type": atype, "bank_name": "Test", "balance": 100})
        assert r.status_code == 201
        assert r.json()["type"] == atype


def test_account_interest_rate(auth_client):
    r = auth_client.post("/api/v1/accounts", json={
        "name": "Festgeld",
        "type": "deposit",
        "bank_name": "ING",
        "balance": 5000,
        "interest_rate": 3.5,
    })
    assert r.status_code == 201
    assert r.json()["interest_rate"] == 3.5
