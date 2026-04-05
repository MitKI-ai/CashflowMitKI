"""Tests for JWT Auth Upgrade — STORY-042"""


def test_token_endpoint_returns_jwt(client, db, admin_user):
    """POST /auth/token with form data returns an access_token."""
    r = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@test.com", "password": "password123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_token_wrong_password(client, db, admin_user):
    r = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@test.com", "password": "wrong"},
    )
    assert r.status_code == 401


def test_me_with_bearer_token(client, db, admin_user):
    """Bearer token from /auth/token works on /auth/me."""
    token_r = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@test.com", "password": "password123"},
    )
    token = token_r.json()["access_token"]
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.com"


def test_bearer_invalid_token_returns_401(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer notavalidtoken"})
    assert r.status_code == 401


def test_bearer_token_works_on_subscriptions(client, db, admin_user, tenant_a):
    """JWT token can access protected subscription endpoint."""
    token_r = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@test.com", "password": "password123"},
    )
    token = token_r.json()["access_token"]
    r = client.get(
        "/api/v1/subscriptions/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


def test_token_response_includes_expiry(client, db, admin_user):
    r = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@test.com", "password": "password123"},
    )
    data = r.json()
    assert "expires_in" in data


def test_session_auth_still_works(auth_client):
    """Existing session-based auth is not broken."""
    r = auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
