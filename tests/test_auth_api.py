"""Tests for auth API — login, register, logout, /me"""


def test_login_success(client, db, admin_user):
    r = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "password123"})
    assert r.status_code == 200
    data = r.json()
    assert data["role"] == "admin"
    assert "user_id" in data


def test_login_wrong_password(client, db, admin_user):
    r = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_email(client):
    r = client.post("/api/v1/auth/login", json={"email": "nobody@test.com", "password": "x"})
    assert r.status_code == 401


def test_me_authenticated(auth_client, admin_user):
    r = auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.com"


def test_me_unauthenticated(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_logout(auth_client):
    r = auth_client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    # After logout, /me should fail
    r2 = auth_client.get("/api/v1/auth/me")
    assert r2.status_code == 401


def test_register_new_tenant(client):
    r = client.post("/api/v1/auth/register", json={
        "tenant_name": "New Corp",
        "display_name": "Owner",
        "email": "owner@newcorp.com",
        "password": "securepass123",
    })
    assert r.status_code == 200
    data = r.json()
    assert "user_id" in data
    assert "tenant_id" in data


def test_register_duplicate_email(client, db, admin_user):
    r = client.post("/api/v1/auth/register", json={
        "tenant_name": "Another Corp",
        "display_name": "Dup",
        "email": "admin@test.com",
        "password": "pass",
    })
    assert r.status_code in (400, 409)


def test_register_duplicate_tenant_slug(client, db, tenant_a):
    r = client.post("/api/v1/auth/register", json={
        "tenant_name": "Acme GmbH",
        "display_name": "Owner",
        "email": "new@unique.com",
        "password": "pass",
    })
    assert r.status_code in (400, 409)
