"""Tests for Transfers — STORY-057"""


def _make_accounts(client):
    a1 = client.post("/api/v1/accounts", json={"name": "Girokonto", "type": "checking", "bank_name": "Sparkasse", "balance": 3200}).json()["id"]
    a2 = client.post("/api/v1/accounts", json={"name": "Sparkonto", "type": "savings", "bank_name": "ING", "balance": 12000}).json()["id"]
    return a1, a2


def test_create_transfer(auth_client):
    a1, a2 = _make_accounts(auth_client)
    r = auth_client.post("/api/v1/transfers", json={
        "from_account_id": a1,
        "to_account_id": a2,
        "amount": 500.00,
        "description": "Sparplan",
        "transfer_date": "2026-03-01",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["amount"] == 500.00
    assert data["from_account_id"] == a1
    assert data["to_account_id"] == a2


def test_same_account_rejected(auth_client):
    a1, _ = _make_accounts(auth_client)
    r = auth_client.post("/api/v1/transfers", json={
        "from_account_id": a1,
        "to_account_id": a1,
        "amount": 100,
        "description": "Self",
        "transfer_date": "2026-03-01",
    })
    assert r.status_code == 400


def test_list_transfers(auth_client):
    a1, a2 = _make_accounts(auth_client)
    auth_client.post("/api/v1/transfers", json={"from_account_id": a1, "to_account_id": a2, "amount": 500, "description": "T1", "transfer_date": "2026-03-01"})
    auth_client.post("/api/v1/transfers", json={"from_account_id": a1, "to_account_id": a2, "amount": 200, "description": "T2", "transfer_date": "2026-03-15"})
    r = auth_client.get("/api/v1/transfers")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_delete_transfer(auth_client):
    a1, a2 = _make_accounts(auth_client)
    create = auth_client.post("/api/v1/transfers", json={"from_account_id": a1, "to_account_id": a2, "amount": 100, "description": "X", "transfer_date": "2026-03-01"})
    tid = create.json()["id"]
    r = auth_client.delete(f"/api/v1/transfers/{tid}")
    assert r.status_code == 200


def test_tenant_isolation_transfers(auth_client, auth_client_b):
    a1, a2 = _make_accounts(auth_client)
    b1 = auth_client_b.post("/api/v1/accounts", json={"name": "B1", "type": "checking", "bank_name": "B", "balance": 0}).json()["id"]
    b2 = auth_client_b.post("/api/v1/accounts", json={"name": "B2", "type": "savings", "bank_name": "B", "balance": 0}).json()["id"]

    auth_client.post("/api/v1/transfers", json={"from_account_id": a1, "to_account_id": a2, "amount": 100, "description": "TA", "transfer_date": "2026-03-01"})
    auth_client_b.post("/api/v1/transfers", json={"from_account_id": b1, "to_account_id": b2, "amount": 200, "description": "TB", "transfer_date": "2026-03-01"})

    descs_a = [t["description"] for t in auth_client.get("/api/v1/transfers").json()]
    assert "TA" in descs_a and "TB" not in descs_a
