"""Tests for Direct Debits CRUD — STORY-056"""


def _make_account(client):
    return client.post("/api/v1/accounts", json={"name": "Girokonto", "type": "checking", "bank_name": "Sparkasse", "balance": 3200}).json()["id"]


def test_create_direct_debit(auth_client):
    acc_id = _make_account(auth_client)
    r = auth_client.post("/api/v1/direct-debits", json={
        "name": "Strom EnBW",
        "creditor": "EnBW Energie",
        "amount": 85.00,
        "frequency": "monthly",
        "expected_day": 5,
        "account_id": acc_id,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Strom EnBW"
    assert data["creditor"] == "EnBW Energie"
    assert data["amount"] == 85.00
    assert data["monthly_amount"] == 85.00


def test_quarterly_normalization(auth_client):
    acc_id = _make_account(auth_client)
    r = auth_client.post("/api/v1/direct-debits", json={
        "name": "GEZ",
        "creditor": "ARD ZDF",
        "amount": 55.08,
        "frequency": "quarterly",
        "expected_day": 15,
        "account_id": acc_id,
    })
    assert r.status_code == 201
    assert r.json()["monthly_amount"] == 18.36  # 55.08 / 3


def test_list_direct_debits(auth_client):
    acc_id = _make_account(auth_client)
    auth_client.post("/api/v1/direct-debits", json={"name": "Strom", "creditor": "EnBW", "amount": 85, "frequency": "monthly", "expected_day": 5, "account_id": acc_id})
    auth_client.post("/api/v1/direct-debits", json={"name": "Internet", "creditor": "Vodafone", "amount": 45, "frequency": "monthly", "expected_day": 3, "account_id": acc_id})
    r = auth_client.get("/api/v1/direct-debits")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_direct_debit(auth_client):
    acc_id = _make_account(auth_client)
    create = auth_client.post("/api/v1/direct-debits", json={"name": "Strom", "creditor": "EnBW", "amount": 85, "frequency": "monthly", "expected_day": 5, "account_id": acc_id})
    dd_id = create.json()["id"]
    r = auth_client.put(f"/api/v1/direct-debits/{dd_id}", json={"amount": 95})
    assert r.status_code == 200
    assert r.json()["amount"] == 95


def test_delete_direct_debit(auth_client):
    acc_id = _make_account(auth_client)
    create = auth_client.post("/api/v1/direct-debits", json={"name": "Test", "creditor": "X", "amount": 10, "frequency": "monthly", "expected_day": 1, "account_id": acc_id})
    dd_id = create.json()["id"]
    r = auth_client.delete(f"/api/v1/direct-debits/{dd_id}")
    assert r.status_code == 200
    assert auth_client.get(f"/api/v1/direct-debits/{dd_id}").status_code == 404


def test_tenant_isolation_direct_debits(auth_client, auth_client_b):
    acc_a = _make_account(auth_client)
    acc_b = auth_client_b.post("/api/v1/accounts", json={"name": "Konto B", "type": "checking", "bank_name": "B", "balance": 0}).json()["id"]

    auth_client.post("/api/v1/direct-debits", json={"name": "DD_A", "creditor": "A", "amount": 50, "frequency": "monthly", "expected_day": 1, "account_id": acc_a})
    auth_client_b.post("/api/v1/direct-debits", json={"name": "DD_B", "creditor": "B", "amount": 60, "frequency": "monthly", "expected_day": 1, "account_id": acc_b})

    names_a = [d["name"] for d in auth_client.get("/api/v1/direct-debits").json()]
    assert "DD_A" in names_a and "DD_B" not in names_a


def test_mandate_reference(auth_client):
    acc_id = _make_account(auth_client)
    r = auth_client.post("/api/v1/direct-debits", json={
        "name": "Strom",
        "creditor": "EnBW",
        "amount": 85,
        "frequency": "monthly",
        "expected_day": 5,
        "account_id": acc_id,
        "mandate_reference": "SEPA-2024-001234",
    })
    assert r.status_code == 201
    assert r.json()["mandate_reference"] == "SEPA-2024-001234"
