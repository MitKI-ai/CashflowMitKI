"""Tests for Fuzzy Matching + Batch Entity Creation + LLM Categorization — STORY-098, 099, 100, 101."""
import io
from unittest.mock import patch

# ── STORY-098: Fuzzy Matching ────────────────────────────────────────

def test_fuzzy_match_partial_name(auth_client):
    """Fuzzy matching catches partial name overlaps."""
    acc = auth_client.post("/api/v1/accounts/", json={"name": "Girokonto", "type": "checking", "bank_name": "Test"}).json()
    auth_client.post("/api/v1/direct-debits/", json={
        "name": "Vodafone Internet", "amount": 45, "frequency": "monthly",
        "expected_day": 3, "account_id": acc["id"],
    })

    csv = """Buchungstag;Verwendungszweck;Betrag
03.03.2026;VODAFONE GMBH INTERNET;-45.00"""

    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("a.csv", io.BytesIO(csv.encode()), "text/csv")},
    )
    entry = r.json()["entries"][0]
    assert entry["match_status"] == "known_expense"
    assert "Vodafone" in entry["matched_entity"]


def test_fuzzy_match_case_insensitive(auth_client):
    acc = auth_client.post("/api/v1/accounts/", json={"name": "Konto", "type": "checking", "bank_name": "T"}).json()
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Gehalt", "type": "income", "amount": 4500,
        "frequency": "monthly", "execution_day": 27, "account_id": acc["id"],
    })

    csv = """Buchungstag;Verwendungszweck;Betrag
27.03.2026;GEHALT ARBEITGEBER AG;4500.00"""

    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("a.csv", io.BytesIO(csv.encode()), "text/csv")},
    )
    assert r.json()["entries"][0]["match_status"] == "known_income"


def test_fuzzy_match_subscription(auth_client):
    """Subscriptions also get matched."""
    auth_client.post("/api/v1/subscriptions/", json={
        "name": "Netflix", "cost": 17.99, "billing_cycle": "monthly",
        "status": "active", "start_date": "2026-01-01",
    })

    csv = """Buchungstag;Verwendungszweck;Betrag
10.03.2026;NETFLIX.COM;-17.99"""

    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("a.csv", io.BytesIO(csv.encode()), "text/csv")},
    )
    entry = r.json()["entries"][0]
    assert entry["match_status"] == "known_expense"
    assert "Netflix" in entry["matched_entity"]


# ── STORY-099: Batch Entity Creation ────────────────────────────────

def test_batch_create_mixed_entities(auth_client):
    """Confirm with mixed actions: transaction + standing_order + direct_debit."""
    auth_client.post("/api/v1/accounts/", json={"name": "Konto", "type": "checking", "bank_name": "Test"})

    r = auth_client.post("/api/v1/import/bank-statement/confirm", json={
        "entries": [
            {"description": "Einkauf REWE", "amount": -45.0, "date": "2026-03-15",
             "action": "transaction", "category": "food"},
            {"description": "Neue Miete", "amount": -1300.0, "date": "2026-03-01",
             "action": "standing_order", "frequency": "monthly"},
            {"description": "Neuer Strom", "amount": -90.0, "date": "2026-03-05",
             "action": "direct_debit", "frequency": "monthly"},
            {"description": "Ignoriert", "amount": -5.0, "date": "2026-03-01", "action": "ignore"},
        ],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["created_transactions"] == 1
    assert data["created_standing_orders"] == 1
    assert data["created_direct_debits"] == 1
    assert data["ignored"] == 1


def test_batch_creates_correct_types(auth_client):
    """Income entries get correct type on standing_order creation."""
    auth_client.post("/api/v1/accounts/", json={"name": "Konto", "type": "checking", "bank_name": "Test"})

    auth_client.post("/api/v1/import/bank-statement/confirm", json={
        "entries": [
            {"description": "Gehalt Firma", "amount": 4500.0, "date": "2026-03-27",
             "action": "standing_order", "frequency": "monthly"},
        ],
    })
    # Verify it was created as income
    sos = auth_client.get("/api/v1/standing-orders/").json()
    gehalt = [s for s in sos if s["name"] == "Gehalt Firma"]
    assert len(gehalt) == 1
    assert gehalt[0]["type"] == "income"


# ── STORY-100: LLM Auto-Categorization ──────────────────────────────

def test_llm_categorize_endpoint(auth_client):
    """LLM categorization endpoint processes entries."""
    auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic", "api_key": "sk-ant-test", "model_id": "claude-sonnet-4-20250514",
    })

    mock_response = {
        "content": '[{"description": "REWE", "category": "food"}, {"description": "Shell Tankstelle", "category": "transport"}]',
        "tool_calls": None,
        "model": "test",
    }
    with patch("app.services.llm_service.LLMService.chat", return_value=mock_response):
        r = auth_client.post("/api/v1/import/bank-statement/categorize", json={
            "entries": [
                {"description": "REWE SAGT DANKE", "amount": -67.50},
                {"description": "Shell Tankstelle 1234", "amount": -55.00},
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert "categories" in data


def test_llm_categorize_without_provider(auth_client):
    r = auth_client.post("/api/v1/import/bank-statement/categorize", json={
        "entries": [{"description": "Test", "amount": -10}],
    })
    assert r.status_code == 404


# ── STORY-101: Import History + Duplicate Detection ─────────────────

def test_import_history_tracked(auth_client):
    csv = """Buchungstag;Verwendungszweck;Betrag
01.03.2026;Test Entry;-10.00"""

    auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("test.csv", io.BytesIO(csv.encode()), "text/csv")},
    )
    r = auth_client.get("/api/v1/import/bank-statement/history")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert data[0]["filename"] == "test.csv"


def test_duplicate_detection(auth_client):
    csv = """Buchungstag;Verwendungszweck;Betrag
01.03.2026;Duplicate Test;-10.00"""

    # Upload once
    auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("dup.csv", io.BytesIO(csv.encode()), "text/csv")},
    )
    # Upload same file again
    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("dup.csv", io.BytesIO(csv.encode()), "text/csv")},
    )
    assert r.status_code == 200
    assert r.json().get("duplicate") is True
