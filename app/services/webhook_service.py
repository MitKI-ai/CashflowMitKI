"""Webhook Service — HMAC-signed outgoing webhooks — STORY-037"""
import hashlib
import hmac
import json
import logging

import httpx
from sqlalchemy.orm import Session

from app.models.webhook import WebhookEndpoint

logger = logging.getLogger(__name__)


class WebhookService:

    @staticmethod
    def dispatch(db: Session, tenant_id: str, event: str, payload: dict) -> list[dict]:
        """Send webhook to all active endpoints subscribed to `event`."""
        endpoints = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.tenant_id == tenant_id,
            WebhookEndpoint.is_active == True,  # noqa: E712
        ).all()

        results = []
        for ep in endpoints:
            subscribed = json.loads(ep.events or '["*"]')
            if "*" not in subscribed and event not in subscribed:
                continue

            body = json.dumps(payload, separators=(",", ":")).encode()
            sig = "sha256=" + hmac.new(ep.secret.encode(), body, hashlib.sha256).hexdigest()
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Event": event,
                "X-Webhook-Signature": sig,
            }
            try:
                resp = httpx.post(ep.url, headers=headers, json=payload, timeout=10)
                results.append({"endpoint_id": ep.id, "status": "sent", "http_status": resp.status_code})
            except Exception as exc:
                logger.warning("Webhook delivery failed for %s: %s", ep.url, exc)
                results.append({"endpoint_id": ep.id, "status": "failed", "error": str(exc)})

        return results
