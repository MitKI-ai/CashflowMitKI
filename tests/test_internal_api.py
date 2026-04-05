"""Tests for Internal API endpoints — STORY-025"""
from datetime import date, timedelta

from tests.conftest import make_subscription

INTERNAL_KEY = "test-internal-key"  # matches conftest.py os.environ["INTERNAL_API_KEY"]


def _headers():
    return {"X-Internal-Key": INTERNAL_KEY}


# ── Auth guard ─────────────────────────────────────────────────────────────────

def test_internal_requires_key(client):
    r = client.post("/api/v1/internal/renewal-reminders")
    assert r.status_code == 401


def test_internal_rejects_wrong_key(client):
    r = client.post("/api/v1/internal/renewal-reminders",
                    headers={"X-Internal-Key": "wrong-key"})
    assert r.status_code == 401


# ── renewal-reminders ──────────────────────────────────────────────────────────

def test_renewal_reminders_returns_count(client, db, admin_user, tenant_a):
    """POST /internal/renewal-reminders returns sent count."""
    from unittest.mock import patch
    make_subscription(db, tenant_a.id, admin_user.id,
                      name="Due Soon",
                      next_renewal=date.today() + timedelta(days=5),
                      status="active")
    with patch("app.api.v1.internal.EmailService.send_renewal_reminder", return_value=True):
        r = client.post("/api/v1/internal/renewal-reminders", headers=_headers())
    assert r.status_code == 200
    data = r.json()
    assert "sent" in data
    assert data["sent"] >= 0


def test_renewal_reminders_skips_non_active(client, db, admin_user, tenant_a):
    """Cancelled subscriptions are not included in reminders."""
    from unittest.mock import patch
    make_subscription(db, tenant_a.id, admin_user.id,
                      name="Cancelled",
                      next_renewal=date.today() + timedelta(days=3),
                      status="cancelled")
    with patch("app.api.v1.internal.EmailService.send_renewal_reminder", return_value=True) as mock_send:
        r = client.post("/api/v1/internal/renewal-reminders", headers=_headers())
    assert r.status_code == 200
    mock_send.assert_not_called()


# ── process-renewals ──────────────────────────────────────────────────────────

def test_process_renewals_returns_summary(client, db, admin_user, tenant_a):
    """POST /internal/process-renewals returns processed/expired counts."""
    r = client.post("/api/v1/internal/process-renewals", headers=_headers())
    assert r.status_code == 200
    data = r.json()
    assert "renewed" in data
    assert "expired" in data


def test_process_renewals_expires_overdue(client, db, admin_user, tenant_a):
    """Subscriptions past end_date with auto_renew=False become expired."""
    from unittest.mock import patch
    make_subscription(db, tenant_a.id, admin_user.id,
                      name="Old Sub",
                      end_date=date.today() - timedelta(days=1),
                      auto_renew=False,
                      status="active")
    with patch("app.api.v1.internal.EmailService.send_expiry_notice", return_value=True):
        r = client.post("/api/v1/internal/process-renewals", headers=_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["expired"] >= 1
