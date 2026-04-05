"""Tests for LLM Provider Management — STORY-086."""


def test_list_providers_empty(auth_client):
    r = auth_client.get("/api/v1/llm/providers")
    assert r.status_code == 200
    assert r.json() == []


def test_create_anthropic_provider(auth_client):
    r = auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic",
        "api_key": "sk-ant-test-key-12345",
        "model_id": "claude-sonnet-4-20250514",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["provider"] == "anthropic"
    assert data["model_id"] == "claude-sonnet-4-20250514"
    assert data["is_active"] is True
    # API key must NOT be in response
    assert "api_key" not in data
    assert "sk-ant" not in str(data)


def test_create_openrouter_provider(auth_client):
    r = auth_client.post("/api/v1/llm/providers", json={
        "provider": "openrouter",
        "api_key": "sk-or-test-key-67890",
        "model_id": "anthropic/claude-sonnet-4-20250514",
    })
    assert r.status_code == 201
    assert r.json()["provider"] == "openrouter"


def test_api_key_never_in_list(auth_client):
    auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic",
        "api_key": "sk-ant-secret-key",
        "model_id": "claude-haiku-4-5-20251001",
    })
    r = auth_client.get("/api/v1/llm/providers")
    for p in r.json():
        assert "api_key" not in p
        assert "secret" not in str(p)


def test_api_key_encrypted_in_db(auth_client, db):
    """Key stored in DB is encrypted, not plaintext."""
    auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic",
        "api_key": "sk-ant-plaintext-key",
        "model_id": "claude-sonnet-4-20250514",
    })
    from app.models.llm_provider import LLMProvider
    provider = db.query(LLMProvider).first()
    assert provider is not None
    # Encrypted value should NOT contain the plaintext
    assert "sk-ant-plaintext-key" not in provider.api_key_encrypted


def test_api_key_decryptable(auth_client, db):
    """Encrypted key can be decrypted back to original."""
    auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic",
        "api_key": "sk-ant-decrypt-test",
        "model_id": "claude-sonnet-4-20250514",
    })
    from app.core.encryption import decrypt_api_key
    from app.models.llm_provider import LLMProvider
    provider = db.query(LLMProvider).first()
    decrypted = decrypt_api_key(provider.api_key_encrypted)
    assert decrypted == "sk-ant-decrypt-test"


def test_update_provider(auth_client):
    create = auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic",
        "api_key": "sk-ant-old-key",
        "model_id": "claude-haiku-4-5-20251001",
    })
    pid = create.json()["id"]
    r = auth_client.put(f"/api/v1/llm/providers/{pid}", json={
        "model_id": "claude-sonnet-4-20250514",
    })
    assert r.status_code == 200
    assert r.json()["model_id"] == "claude-sonnet-4-20250514"


def test_delete_provider(auth_client):
    create = auth_client.post("/api/v1/llm/providers", json={
        "provider": "openrouter",
        "api_key": "sk-or-delete-me",
        "model_id": "test/model",
    })
    pid = create.json()["id"]
    r = auth_client.delete(f"/api/v1/llm/providers/{pid}")
    assert r.status_code == 200
    # Verify deleted
    r2 = auth_client.get("/api/v1/llm/providers")
    ids = [p["id"] for p in r2.json()]
    assert pid not in ids


def test_provider_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/llm/providers", json={
        "provider": "anthropic",
        "api_key": "sk-ant-tenant-a",
        "model_id": "claude-sonnet-4-20250514",
    })
    r = auth_client_b.get("/api/v1/llm/providers")
    assert r.json() == []


def test_invalid_provider_rejected(auth_client):
    r = auth_client.post("/api/v1/llm/providers", json={
        "provider": "invalid_provider",
        "api_key": "some-key",
        "model_id": "some-model",
    })
    assert r.status_code == 400
