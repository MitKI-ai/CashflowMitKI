"""Tests for Chat Tool Definitions + Chat API — STORY-090, 091."""
from unittest.mock import patch


def test_tool_definitions_endpoint(auth_client):
    """List all available tool definitions."""
    r = auth_client.get("/api/v1/llm/tools")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 10
    tool_names = [t["name"] for t in data]
    assert "create_account" in tool_names
    assert "create_standing_order" in tool_names
    assert "create_direct_debit" in tool_names
    assert "create_transaction" in tool_names
    assert "create_investment" in tool_names
    assert "create_savings_goal" in tool_names
    assert "list_accounts" in tool_names


def test_tool_definition_has_schema(auth_client):
    r = auth_client.get("/api/v1/llm/tools")
    for tool in r.json():
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool


def test_chat_endpoint_requires_provider(auth_client):
    """Chat without configured provider returns error."""
    r = auth_client.post("/api/v1/llm/chat", json={
        "message": "Hallo",
    })
    assert r.status_code == 404


def test_chat_endpoint_with_mock_provider(auth_client):
    """Chat with mocked LLM returns response."""
    auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic",
        "api_key": "sk-ant-test",
        "model_id": "claude-sonnet-4-20250514",
    })
    with patch("app.services.llm_service.LLMService.chat",
               return_value={"content": "Ich helfe dir gerne!", "tool_calls": None, "model": "test"}):
        r = auth_client.post("/api/v1/llm/chat", json={
            "message": "Hallo, wie geht es?",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["response"] == "Ich helfe dir gerne!"


def test_chat_with_tool_call_creates_entity(auth_client):
    """When LLM returns tool_use, the tool gets executed."""
    auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic",
        "api_key": "sk-ant-test",
        "model_id": "claude-sonnet-4-20250514",
    })
    tool_response = {
        "content": None,
        "tool_calls": [{"id": "call_1", "name": "create_account",
                        "input": {"name": "Chat-Konto", "type": "checking", "bank_name": "Testbank", "balance": 1500.0}}],
        "model": "test",
    }
    confirm_response = {
        "content": "Girokonto 'Chat-Konto' mit 1500€ wurde erstellt!",
        "tool_calls": None,
        "model": "test",
    }
    with patch("app.services.llm_service.LLMService.chat", side_effect=[tool_response, confirm_response]):
        r = auth_client.post("/api/v1/llm/chat", json={
            "message": "Erstelle ein Girokonto bei der Testbank mit 1500€",
            "auto_execute": True,
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("tool_results") is not None or data.get("response") is not None

    # Verify account was created
    accounts = auth_client.get("/api/v1/accounts/").json()
    assert any(a["name"] == "Chat-Konto" for a in accounts)


def test_chat_settings_page_renders(auth_client):
    r = auth_client.get("/settings")
    assert r.status_code == 200
    assert "LLM" in r.text or "API-Key" in r.text or "Provider" in r.text
