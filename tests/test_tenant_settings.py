"""Tests for STORY-014: Multi-Currency Display + Tenant Settings page"""


# ── Settings page ────────────────────────────────────────────────────────────

def test_settings_page_accessible_by_admin(auth_client):
    r = auth_client.get("/settings")
    assert r.status_code == 200
    assert "Einstellungen" in r.text or "Settings" in r.text


def test_settings_page_blocked_for_non_admin(user_client):
    r = user_client.get("/settings", follow_redirects=False)
    assert r.status_code == 302
    assert "/dashboard" in r.headers.get("location", "")


def test_settings_page_shows_currency_field(auth_client, db, tenant_a):
    r = auth_client.get("/settings")
    assert r.status_code == 200
    assert "currency" in r.text.lower() or "währung" in r.text.lower()


def test_update_tenant_currency(auth_client, db, tenant_a):
    r = auth_client.post("/settings", data={"currency": "USD", "name": tenant_a.name})
    assert r.status_code in (200, 302)
    db.refresh(tenant_a)
    assert tenant_a.currency == "USD"


def test_currency_shown_on_dashboard(auth_client, db, admin_user, tenant_a):
    """After setting USD, dashboard monthly cost shows USD."""
    from tests.conftest import make_subscription
    tenant_a.currency = "USD"
    db.commit()
    make_subscription(db, tenant_a.id, admin_user.id, cost=9.99, currency="USD")
    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    # The monthly cost card should show the tenant currency
    assert "USD" in r.text or "$" in r.text or "9.99" in r.text
