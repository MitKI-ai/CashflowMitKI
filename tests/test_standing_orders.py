"""Tests for Standing Orders CRUD — STORY-055"""


def _make_account(client):
    r = client.post("/api/v1/accounts", json={"name": "Girokonto", "type": "checking", "bank_name": "Sparkasse", "balance": 3200})
    return r.json()["id"]


def test_create_standing_order_income(auth_client):
    acc_id = _make_account(auth_client)
    r = auth_client.post("/api/v1/standing-orders", json={
        "name": "Gehalt",
        "type": "income",
        "recipient": "Arbeitgeber AG",
        "amount": 4500.00,
        "frequency": "monthly",
        "execution_day": 27,
        "account_id": acc_id,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Gehalt"
    assert data["type"] == "income"
    assert data["amount"] == 4500.00
    assert data["execution_day"] == 27
    assert data["monthly_amount"] == 4500.00


def test_create_standing_order_expense(auth_client):
    acc_id = _make_account(auth_client)
    r = auth_client.post("/api/v1/standing-orders", json={
        "name": "Miete",
        "type": "expense",
        "recipient": "Vermieter GmbH",
        "amount": 1200.00,
        "frequency": "monthly",
        "execution_day": 1,
        "account_id": acc_id,
    })
    assert r.status_code == 201
    assert r.json()["type"] == "expense"


def test_yearly_normalization(auth_client):
    acc_id = _make_account(auth_client)
    r = auth_client.post("/api/v1/standing-orders", json={
        "name": "KFZ-Versicherung",
        "type": "expense",
        "amount": 600.00,
        "frequency": "yearly",
        "execution_day": 1,
        "account_id": acc_id,
    })
    assert r.status_code == 201
    assert r.json()["monthly_amount"] == 50.00  # 600 / 12


def test_quarterly_normalization(auth_client):
    acc_id = _make_account(auth_client)
    r = auth_client.post("/api/v1/standing-orders", json={
        "name": "Versicherung",
        "type": "expense",
        "amount": 300.00,
        "frequency": "quarterly",
        "execution_day": 1,
        "account_id": acc_id,
    })
    assert r.status_code == 201
    assert r.json()["monthly_amount"] == 100.00  # 300 / 3


def test_list_standing_orders(auth_client):
    acc_id = _make_account(auth_client)
    auth_client.post("/api/v1/standing-orders", json={"name": "Gehalt", "type": "income", "amount": 4500, "frequency": "monthly", "execution_day": 27, "account_id": acc_id})
    auth_client.post("/api/v1/standing-orders", json={"name": "Miete", "type": "expense", "amount": 1200, "frequency": "monthly", "execution_day": 1, "account_id": acc_id})

    r = auth_client.get("/api/v1/standing-orders")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_standing_order(auth_client):
    acc_id = _make_account(auth_client)
    create = auth_client.post("/api/v1/standing-orders", json={"name": "Miete", "type": "expense", "amount": 1200, "frequency": "monthly", "execution_day": 1, "account_id": acc_id})
    so_id = create.json()["id"]

    r = auth_client.put(f"/api/v1/standing-orders/{so_id}", json={"amount": 1300})
    assert r.status_code == 200
    assert r.json()["amount"] == 1300


def test_delete_standing_order(auth_client):
    acc_id = _make_account(auth_client)
    create = auth_client.post("/api/v1/standing-orders", json={"name": "Test", "type": "expense", "amount": 100, "frequency": "monthly", "execution_day": 1, "account_id": acc_id})
    so_id = create.json()["id"]

    r = auth_client.delete(f"/api/v1/standing-orders/{so_id}")
    assert r.status_code == 200

    r2 = auth_client.get(f"/api/v1/standing-orders/{so_id}")
    assert r2.status_code == 404


def test_tenant_isolation_standing_orders(auth_client, auth_client_b):
    acc_a = _make_account(auth_client)
    acc_b = auth_client_b.post("/api/v1/accounts", json={"name": "Konto B", "type": "checking", "bank_name": "B", "balance": 0}).json()["id"]

    auth_client.post("/api/v1/standing-orders", json={"name": "SO_A", "type": "income", "amount": 100, "frequency": "monthly", "execution_day": 1, "account_id": acc_a})
    auth_client_b.post("/api/v1/standing-orders", json={"name": "SO_B", "type": "income", "amount": 200, "frequency": "monthly", "execution_day": 1, "account_id": acc_b})

    names_a = [s["name"] for s in auth_client.get("/api/v1/standing-orders").json()]
    names_b = [s["name"] for s in auth_client_b.get("/api/v1/standing-orders").json()]

    assert "SO_A" in names_a and "SO_B" not in names_a
    assert "SO_B" in names_b and "SO_A" not in names_b
