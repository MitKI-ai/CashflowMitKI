"""Tests for LLM Service (Claude SDK + OpenRouter) — STORY-087, 088."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_llm_service_anthropic_chat():
    """Anthropic provider creates correct client."""
    from app.services.llm_service import LLMService

    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text="Hallo! Wie kann ich helfen?")]
    mock_response.stop_reason = "end_turn"
    mock_response.model = "claude-sonnet-4-20250514"

    with patch("app.services.llm_service.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = mock_response

        result = LLMService.chat(
            provider="anthropic",
            api_key="sk-ant-test",
            model_id="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hallo"}],
        )
        assert result["content"] == "Hallo! Wie kann ich helfen?"
        assert result["model"] == "claude-sonnet-4-20250514"
        instance.messages.create.assert_called_once()


def test_llm_service_openrouter_chat():
    """OpenRouter provider uses OpenAI SDK with custom base_url."""
    from app.services.llm_service import LLMService

    mock_choice = MagicMock()
    mock_choice.message.content = "OpenRouter response"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.model = "anthropic/claude-sonnet-4-20250514"

    with patch("app.services.llm_service.openai.OpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create.return_value = mock_response

        result = LLMService.chat(
            provider="openrouter",
            api_key="sk-or-test",
            model_id="anthropic/claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert result["content"] == "OpenRouter response"
        MockClient.assert_called_once_with(
            api_key="sk-or-test",
            base_url="https://openrouter.ai/api/v1",
        )


def test_llm_service_with_tools():
    """Chat with tool definitions passes them correctly."""
    from app.services.llm_service import LLMService

    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text="Ich erstelle das Konto.")]
    mock_response.stop_reason = "end_turn"
    mock_response.model = "claude-sonnet-4-20250514"

    tools = [{"name": "create_account", "description": "Create bank account",
              "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}}}]

    with patch("app.services.llm_service.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = mock_response

        result = LLMService.chat(
            provider="anthropic",
            api_key="sk-ant-test",
            model_id="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Erstelle ein Girokonto"}],
            tools=tools,
        )
        assert result["content"] == "Ich erstelle das Konto."
        call_kwargs = instance.messages.create.call_args[1]
        assert "tools" in call_kwargs


def test_llm_service_tool_use_response():
    """When LLM returns tool_use, service extracts tool calls."""
    from app.services.llm_service import LLMService

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "call_123"
    tool_block.name = "create_account"
    tool_block.input = {"name": "Girokonto", "type": "checking", "balance": 3200}

    mock_response = MagicMock()
    mock_response.content = [tool_block]
    mock_response.stop_reason = "tool_use"
    mock_response.model = "claude-sonnet-4-20250514"

    with patch("app.services.llm_service.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = mock_response

        result = LLMService.chat(
            provider="anthropic",
            api_key="sk-ant-test",
            model_id="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Erstelle Girokonto mit 3200€"}],
            tools=[{"name": "create_account", "description": "...", "input_schema": {}}],
        )
        assert result["tool_calls"] is not None
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "create_account"
        assert result["tool_calls"][0]["input"]["balance"] == 3200


def test_llm_test_connection_api(auth_client):
    """POST /api/v1/llm/test validates connection."""
    with patch("app.services.llm_service.LLMService.chat", return_value={"content": "OK", "model": "test"}):
        # First create a provider
        auth_client.post("/api/v1/llm/providers", json={
            "provider": "anthropic",
            "api_key": "sk-ant-test",
            "model_id": "claude-sonnet-4-20250514",
        })
        r = auth_client.post("/api/v1/llm/test")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_llm_test_no_provider(auth_client):
    """Test without configured provider returns error."""
    r = auth_client.post("/api/v1/llm/test")
    assert r.status_code == 404
