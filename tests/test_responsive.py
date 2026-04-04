"""Tests for STORY-015: Responsive Layout — hamburger menu for mobile"""


def test_nav_has_mobile_menu_toggle(auth_client):
    """Authenticated pages must have a mobile nav hamburger button."""
    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    assert "mobile-menu" in r.text


def test_nav_has_mobile_menu_links(auth_client):
    """Mobile menu must contain navigation links."""
    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    # The mobile menu div is present
    assert 'id="mobile-menu"' in r.text
    assert "/subscriptions" in r.text
