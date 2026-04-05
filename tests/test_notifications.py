"""Tests for STORY-020: In-App Notifications API + Bell Icon + Polling"""


def _create_notification(auth_client, title="Test", message="Hello"):
    """Helper: create a notification via the internal API."""
    return auth_client.post("/api/v1/notifications/", json={
        "title": title, "message": message, "type": "info",
    })


# ── Notification CRUD API ─────────────────────────────────────────────────────

def test_create_notification(auth_client):
    r = _create_notification(auth_client)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Test"
    assert data["is_read"] is False


def test_list_notifications(auth_client):
    _create_notification(auth_client, title="N1")
    _create_notification(auth_client, title="N2")
    r = auth_client.get("/api/v1/notifications/")
    assert r.status_code == 200
    titles = [n["title"] for n in r.json()]
    assert "N1" in titles
    assert "N2" in titles


def test_unread_count(auth_client):
    _create_notification(auth_client, title="Unread")
    r = auth_client.get("/api/v1/notifications/unread-count")
    assert r.status_code == 200
    assert r.json()["count"] >= 1


def test_mark_notification_read(auth_client):
    r = _create_notification(auth_client)
    notif_id = r.json()["id"]
    r2 = auth_client.post(f"/api/v1/notifications/{notif_id}/read")
    assert r2.status_code == 200
    assert r2.json()["is_read"] is True


def test_mark_all_read(auth_client):
    _create_notification(auth_client, title="A")
    _create_notification(auth_client, title="B")
    r = auth_client.post("/api/v1/notifications/mark-all-read")
    assert r.status_code == 200
    r2 = auth_client.get("/api/v1/notifications/unread-count")
    assert r2.json()["count"] == 0


def test_notification_tenant_isolation(auth_client, auth_client_b):
    _create_notification(auth_client, title="Tenant A only")
    r = auth_client_b.get("/api/v1/notifications/")
    assert r.status_code == 200
    assert len(r.json()) == 0


# ── Bell icon in base template ────────────────────────────────────────────────

def test_bell_icon_in_navbar(auth_client):
    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    assert "notification" in r.text.lower() or "bell" in r.text.lower() or "unread-count" in r.text
