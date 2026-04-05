"""Tests for Chat Entity CRUD — STORY-092, 093, 094."""
from unittest.mock import patch
import pytest


def _setup_provider(auth_client):
    auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic", "api_key": "sk-ant-test", "model_id": "claude-sonnet-4-20250514",
    })


def _mock_tool_call(name, inp):
    return {
        "content": None,
        "tool_calls": [{"id": "call_1", "name": name, "input": inp}],
        "model": "test",
    }


def _mock_text(text):
    return {"content": text, "tool_calls": None, "model": "test"}


# ── STORY-092: Konten, Daueraufträge, Lastschriften ─────────────────

def test_chat_create_account(auth_client):
    _setup_provider(auth_client)
    tool = _mock_tool_call("create_account", {"name": "ING Girokonto", "type": "checking", "bank_name": "ING", "balance": 2500})
    confirm = _mock_text("Girokonto 'ING Girokonto' mit 2500€ erstellt!")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "Erstelle ING Girokonto mit 2500€", "auto_execute": True})
        assert r.status_code == 200
        assert r.json()["tool_results"][0]["tool"] == "create_account"
    accounts = auth_client.get("/api/v1/accounts/").json()
    assert any(a["name"] == "ING Girokonto" for a in accounts)


def test_chat_list_accounts(auth_client):
    _setup_provider(auth_client)
    auth_client.post("/api/v1/accounts/", json={"name": "TestKonto", "type": "checking", "bank_name": "Test"})
    tool = _mock_tool_call("list_accounts", {})
    confirm = _mock_text("Du hast 1 Konto: TestKonto")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "Zeige meine Konten", "auto_execute": True})
        assert r.status_code == 200


def test_chat_create_standing_order(auth_client):
    _setup_provider(auth_client)
    auth_client.post("/api/v1/accounts/", json={"name": "Konto", "type": "checking", "bank_name": "Test"})
    tool = _mock_tool_call("create_standing_order", {"name": "Gehalt", "type": "income", "amount": 4500, "execution_day": 27})
    confirm = _mock_text("Dauerauftrag 'Gehalt' 4500€ am 27. erstellt!")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "Gehalt 4500 am 27.", "auto_execute": True})
        assert r.json()["tool_results"][0]["result"]["created"] == "standing_order"


def test_chat_create_direct_debit(auth_client):
    _setup_provider(auth_client)
    auth_client.post("/api/v1/accounts/", json={"name": "Konto", "type": "checking", "bank_name": "Test"})
    tool = _mock_tool_call("create_direct_debit", {"name": "Strom EnBW", "amount": 85, "creditor": "EnBW", "expected_day": 5})
    confirm = _mock_text("Lastschrift 'Strom EnBW' 85€ am 5. erstellt!")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "Strom 85€ am 5.", "auto_execute": True})
        assert r.json()["tool_results"][0]["result"]["created"] == "direct_debit"


# ── STORY-093: Transaktionen, Investments, Sparziele ────────────────

def test_chat_create_transaction(auth_client):
    _setup_provider(auth_client)
    tool = _mock_tool_call("create_transaction", {
        "description": "Rewe Einkauf", "amount": 67.50, "type": "expense",
        "category": "food", "transaction_date": "2026-03-30",
    })
    confirm = _mock_text("Ausgabe 67.50€ Rewe Einkauf gespeichert!")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "67.50 bei Rewe für Lebensmittel", "auto_execute": True})
        assert r.json()["tool_results"][0]["result"]["created"] == "transaction"


def test_chat_create_investment(auth_client):
    _setup_provider(auth_client)
    tool = _mock_tool_call("create_investment", {
        "name": "MSCI World ETF", "type": "etf", "current_value": 15000, "invested_amount": 12000, "broker": "Trade Republic",
    })
    confirm = _mock_text("ETF 'MSCI World' angelegt!")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "ETF MSCI World 15000€ wert, 12000 eingezahlt", "auto_execute": True})
        assert r.json()["tool_results"][0]["result"]["created"] == "investment"


def test_chat_create_savings_goal(auth_client):
    _setup_provider(auth_client)
    tool = _mock_tool_call("create_savings_goal", {"name": "Notgroschen", "type": "emergency", "target_amount": 10000, "current_amount": 3000})
    confirm = _mock_text("Sparziel Notgroschen: 3000/10000€")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "Notgroschen 10000€, aktuell 3000", "auto_execute": True})
        assert r.json()["tool_results"][0]["result"]["created"] == "savings_goal"


def test_chat_update_savings_goal(auth_client):
    _setup_provider(auth_client)
    auth_client.post("/api/v1/savings-goals/", json={"name": "Urlaub", "type": "vacation_luxury", "target_amount": 3000, "current_amount": 500})
    tool = _mock_tool_call("update_savings_goal", {"name": "Urlaub", "current_amount": 1200})
    confirm = _mock_text("Sparziel Urlaub auf 1200€ aktualisiert!")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "Urlaub-Sparziel auf 1200 aktualisieren", "auto_execute": True})
        assert r.json()["tool_results"][0]["result"]["updated"] == "savings_goal"


def test_chat_get_cashflow_summary(auth_client):
    _setup_provider(auth_client)
    tool = _mock_tool_call("get_cashflow_summary", {})
    confirm = _mock_text("Dein Cashflow: 0€ netto")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "Wie ist mein Cashflow?", "auto_execute": True})
        assert r.status_code == 200


def test_chat_create_budget_alert(auth_client):
    _setup_provider(auth_client)
    tool = _mock_tool_call("create_budget_alert", {"name": "Essen gehen", "category": "dining", "monthly_limit": 200})
    confirm = _mock_text("Budget-Warnung bei 200€/Monat für Essen gehen erstellt!")
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool, confirm]):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "Warnung bei über 200€ Essen gehen", "auto_execute": True})
        assert r.json()["tool_results"][0]["result"]["created"] == "budget_alert"


# ── STORY-094: Bestätigungs-Flow ────────────────────────────────────

def test_chat_without_auto_execute_returns_preview(auth_client):
    """Without auto_execute, tool calls are returned but NOT executed."""
    _setup_provider(auth_client)
    tool = _mock_tool_call("create_account", {"name": "Preview-Konto", "type": "checking", "balance": 999})
    with patch("app.services.llm_service.LLMService.chat", return_value=tool):
        r = auth_client.post("/api/v1/llm/chat", json={"message": "Erstelle Konto", "auto_execute": False})
        assert r.status_code == 200
        data = r.json()
        assert data["tool_calls"] is not None
        assert data["tool_calls"][0]["name"] == "create_account"
        # Entity should NOT be created
    accounts = auth_client.get("/api/v1/accounts/").json()
    assert not any(a["name"] == "Preview-Konto" for a in accounts)


def test_chat_context_injection(auth_client):
    """Chat endpoint injects current financial context into system prompt."""
    _setup_provider(auth_client)
    auth_client.post("/api/v1/accounts/", json={"name": "Kontext-Konto", "type": "checking", "bank_name": "Test", "balance": 5000})

    with patch("app.services.llm_service.LLMService.chat", return_value=_mock_text("Du hast 5000€")) as mock:
        auth_client.post("/api/v1/llm/chat", json={"message": "Wie viel habe ich?"})
        call_kwargs = mock.call_args[1]
        system = call_kwargs.get("system_prompt", "")
        assert "5000" in system or "Kontext-Konto" in system
