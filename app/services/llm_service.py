"""LLM Service — Anthropic Claude SDK + OpenRouter (OpenAI-compatible)."""
import logging

import anthropic
import openai

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du bist ein Finanz-Assistent für den mitKI.ai Cashflow & Retirement Planner.
Du hilfst Nutzern ihre Finanzdaten zu verwalten: Konten, Daueraufträge, Lastschriften,
Transaktionen, Geldanlagen und Sparziele. Antworte auf Deutsch, kurz und hilfreich.
Wenn der Nutzer eine Aktion wünscht (erstellen, ändern, löschen), nutze die verfügbaren Tools."""


class LLMService:
    SYSTEM_PROMPT = SYSTEM_PROMPT
    @staticmethod
    def chat(
        *,
        provider: str,
        api_key: str,
        model_id: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = 1024,
    ) -> dict:
        if provider == "anthropic":
            return LLMService._chat_anthropic(
                api_key=api_key, model_id=model_id, messages=messages,
                tools=tools, system_prompt=system_prompt, max_tokens=max_tokens,
            )
        elif provider == "openrouter":
            return LLMService._chat_openrouter(
                api_key=api_key, model_id=model_id, messages=messages,
                tools=tools, system_prompt=system_prompt, max_tokens=max_tokens,
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    def _chat_anthropic(*, api_key, model_id, messages, tools, system_prompt, max_tokens) -> dict:
        client = anthropic.Anthropic(api_key=api_key)
        kwargs = {
            "model": model_id,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = client.messages.create(**kwargs)

        # Extract content
        text_parts = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return {
            "content": "".join(text_parts) if text_parts else None,
            "tool_calls": tool_calls if tool_calls else None,
            "stop_reason": response.stop_reason,
            "model": response.model,
        }

    @staticmethod
    def _chat_openrouter(*, api_key, model_id, messages, tools, system_prompt, max_tokens) -> dict:
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        all_messages = [{"role": "system", "content": system_prompt}] + messages
        kwargs = {
            "model": model_id,
            "max_tokens": max_tokens,
            "messages": all_messages,
        }
        if tools:
            # Convert Anthropic tool format to OpenAI format
            kwargs["tools"] = [
                {"type": "function", "function": {"name": t["name"], "description": t.get("description", ""),
                                                   "parameters": t.get("input_schema", {})}}
                for t in tools
            ]

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls = None
        if choice.message.tool_calls:
            import json
            tool_calls = [
                {"id": tc.id, "name": tc.function.name,
                 "input": json.loads(tc.function.arguments) if tc.function.arguments else {}}
                for tc in choice.message.tool_calls
            ]

        return {
            "content": choice.message.content,
            "tool_calls": tool_calls,
            "stop_reason": choice.finish_reason,
            "model": response.model,
        }
