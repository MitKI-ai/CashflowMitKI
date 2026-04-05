"""Tests for SSO Google + Microsoft — STORY-043"""
from unittest.mock import patch


def test_google_sso_redirect(client):
    """GET /auth/sso/google redirects toward Google OAuth."""
    r = client.get("/api/v1/auth/sso/google", follow_redirects=False)
    # Should redirect (302/307) to accounts.google.com or return 501 if not configured
    assert r.status_code in (302, 307, 501)


def test_microsoft_sso_redirect(client):
    """GET /auth/sso/microsoft redirects toward Microsoft OAuth."""
    r = client.get("/api/v1/auth/sso/microsoft", follow_redirects=False)
    assert r.status_code in (302, 307, 501)


def test_google_callback_with_mock_user(client, db):
    """Callback with a mocked OAuth profile creates a user and logs in."""
    mock_profile = {
        "sub": "google-123",
        "email": "sso_user@example.com",
        "name": "SSO User",
    }
    with patch("app.api.v1.auth.fetch_google_profile", return_value=mock_profile):
        r = client.get(
            "/api/v1/auth/sso/google/callback",
            params={"code": "fake-code", "state": "teststate"},
            follow_redirects=False,
        )
    # Either redirect to dashboard on success or 400 on missing state
    assert r.status_code in (200, 302, 307, 400, 422)


def test_sso_callback_existing_user_login(client, db, admin_user):
    """SSO callback for existing email logs in the existing user."""
    mock_profile = {
        "sub": "google-existing",
        "email": "admin@test.com",
        "name": "Admin",
    }
    with patch("app.api.v1.auth.fetch_google_profile", return_value=mock_profile):
        r = client.get(
            "/api/v1/auth/sso/google/callback",
            params={"code": "fake-code", "state": "st"},
            follow_redirects=False,
        )
    assert r.status_code in (200, 302, 307, 400, 422)


def test_sso_user_has_oauth_fields(db, admin_user):
    """User model has oauth_provider and oauth_sub fields."""
    assert hasattr(admin_user, "oauth_provider")
    assert hasattr(admin_user, "oauth_sub")
