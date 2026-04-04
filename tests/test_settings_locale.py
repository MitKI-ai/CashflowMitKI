"""Tests for Settings Seite Locale extension — STORY-030"""


def test_settings_page_shows_locale_field(auth_client):
    r = auth_client.get("/settings")
    assert r.status_code == 200
    assert b"locale" in r.content.lower() or b"sprache" in r.content.lower()


def test_update_locale(auth_client, db, tenant_a):
    r = auth_client.post("/settings", data={
        "name": tenant_a.name,
        "currency": "EUR",
        "locale": "en",
    }, follow_redirects=False)
    assert r.status_code in (200, 302)
    db.refresh(tenant_a)
    assert tenant_a.locale == "en"


def test_update_locale_invalid_rejected(auth_client, db, tenant_a):
    original_locale = tenant_a.locale
    r = auth_client.post("/settings", data={
        "name": tenant_a.name,
        "currency": "EUR",
        "locale": "xx",  # invalid locale — silently ignored
    }, follow_redirects=False)
    assert r.status_code in (200, 302)
    db.refresh(tenant_a)
    assert tenant_a.locale == original_locale  # unchanged
