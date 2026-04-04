"""Tests for Landing Page — STORY-046"""


def test_landing_page_returns_200(client):
    """Root URL returns the public landing page."""
    r = client.get("/")
    assert r.status_code == 200


def test_landing_page_is_public(client):
    """Landing page does not require authentication."""
    r = client.get("/")
    assert r.status_code == 200
    # Should NOT redirect to login
    assert "/login" not in str(r.url)


def test_landing_page_has_signup_cta(client):
    """Landing page contains a sign-up / get-started call-to-action."""
    r = client.get("/")
    body = r.text.lower()
    assert "register" in body or "signup" in body or "starten" in body or "start" in body


def test_landing_page_has_product_name(client):
    """Landing page shows the product name."""
    r = client.get("/")
    assert "Subscription Manager" in r.text or "mitKI" in r.text


def test_landing_page_has_features_section(client):
    """Landing page mentions key features."""
    r = client.get("/")
    body = r.text.lower()
    assert any(kw in body for kw in ["feature", "mrr", "subscription", "abo", "team"])


def test_landing_page_links_to_login(client):
    """Landing page contains a link to login."""
    r = client.get("/")
    assert "/login" in r.text


def test_dashboard_redirects_to_login_when_unauthenticated(client):
    """Unauthenticated /dashboard redirects to login, not landing page."""
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code in (302, 307)
