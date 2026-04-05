"""Tests for Outgoing Webhooks HMAC — STORY-037"""
import hashlib
import hmac
import json
from unittest.mock import patch, MagicMock


def _endpoint_payload(**kwargs):
    defaults = {"url": "https://example.com/webhook", "events": ["subscription.created"], "is_active": True}
    defaults.update(kwargs)
    return defaults


# ── CRUD ─────────────────────────────────────────────────────────────────────

def test_create_webhook_endpoint(auth_client):
    r = auth_client.post("/api/v1/webhooks/", json=_endpoint_payload())
    assert r.status_code == 201
    data = r.json()
    assert data["url"] == "https://example.com/webhook"
    assert "secret" not in data  # secret must not leak


def test_create_webhook_requires_admin(user_client):
    r = user_client.post("/api/v1/webhooks/", json=_endpoint_payload())
    assert r.status_code == 403


def test_list_webhooks(auth_client):
    auth_client.post("/api/v1/webhooks/", json=_endpoint_payload(url="https://a.com/wh"))
    auth_client.post("/api/v1/webhooks/", json=_endpoint_payload(url="https://b.com/wh"))
    r = auth_client.get("/api/v1/webhooks/")
    assert r.status_code == 200
    urls = [w["url"] for w in r.json()]
    assert "https://a.com/wh" in urls


def test_delete_webhook(auth_client):
    r = auth_client.post("/api/v1/webhooks/", json=_endpoint_payload())
    wh_id = r.json()["id"]
    r2 = auth_client.delete(f"/api/v1/webhooks/{wh_id}")
    assert r2.status_code == 200


def test_webhook_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/webhooks/", json=_endpoint_payload(url="https://tenant-a.com/wh"))
    r = auth_client_b.get("/api/v1/webhooks/")
    assert r.status_code == 200
    assert len(r.json()) == 0


# ── HMAC signing ─────────────────────────────────────────────────────────────

def test_webhook_dispatch_sends_post(auth_client, db, admin_user, tenant_a):
    """WebhookService.dispatch sends HTTP POST with HMAC signature."""
    from app.models.webhook import WebhookEndpoint
    wh = WebhookEndpoint(
        tenant_id=tenant_a.id,
        url="https://example.com/wh",
        secret="test-secret",
        events=json.dumps(["subscription.created"]),
        is_active=True,
    )
    db.add(wh)
    db.commit()

    payload = {"event": "subscription.created", "data": {"id": "abc"}}
    with patch("app.services.webhook_service.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        from app.services.webhook_service import WebhookService
        results = WebhookService.dispatch(db, tenant_a.id, "subscription.created", payload)

    assert len(results) == 1
    assert results[0]["status"] == "sent"
    call_kwargs = mock_post.call_args[1]
    assert "headers" in call_kwargs
    assert "X-Webhook-Signature" in call_kwargs["headers"]


def test_webhook_hmac_signature_correct(auth_client, db, admin_user, tenant_a):
    """Verify the HMAC-SHA256 signature matches expected value."""
    from app.models.webhook import WebhookEndpoint
    secret = "my-webhook-secret"
    wh = WebhookEndpoint(
        tenant_id=tenant_a.id,
        url="https://example.com/wh2",
        secret=secret,
        events=json.dumps(["subscription.updated"]),
        is_active=True,
    )
    db.add(wh)
    db.commit()

    payload = {"event": "subscription.updated", "data": {}}
    sent_headers = {}

    def capture_post(url, *, headers, json, timeout):
        sent_headers.update(headers)
        return MagicMock(status_code=200)

    with patch("app.services.webhook_service.httpx.post", side_effect=capture_post):
        from app.services.webhook_service import WebhookService
        WebhookService.dispatch(db, tenant_a.id, "subscription.updated", payload)

    sig = sent_headers.get("X-Webhook-Signature", "")
    body = json.dumps(payload, separators=(",", ":")).encode()
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert sig == expected


def test_inactive_webhook_not_triggered(auth_client, db, admin_user, tenant_a):
    from app.models.webhook import WebhookEndpoint
    wh = WebhookEndpoint(
        tenant_id=tenant_a.id,
        url="https://inactive.com/wh",
        secret="s",
        events=json.dumps(["subscription.created"]),
        is_active=False,
    )
    db.add(wh)
    db.commit()

    with patch("app.services.webhook_service.httpx.post") as mock_post:
        from app.services.webhook_service import WebhookService
        results = WebhookService.dispatch(db, tenant_a.id, "subscription.created", {})

    mock_post.assert_not_called()
    assert len(results) == 0
