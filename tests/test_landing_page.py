"""Tests for root route — STORY-046 (landing page deprecated, root now redirects to /login)."""


def test_root_redirects_unauthenticated_to_login(client):
    """Unauthenticated root URL redirects to /login."""
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/login"


def test_root_follow_redirect_reaches_login(client):
    """Following the root redirect ends on the login page."""
    r = client.get("/")
    assert r.status_code == 200
    assert "/login" in str(r.url)


def test_dashboard_redirects_to_login_when_unauthenticated(client):
    """Unauthenticated /dashboard redirects to login."""
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code in (302, 307)
