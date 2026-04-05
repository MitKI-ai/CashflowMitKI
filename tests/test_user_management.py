"""Tests for User Management — STORY-027"""


def test_list_users_admin(auth_client, admin_user, regular_user):
    r = auth_client.get("/api/v1/users/")
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert "admin@test.com" in emails
    assert "user@test.com" in emails


def test_list_users_requires_admin(user_client):
    r = user_client.get("/api/v1/users/")
    assert r.status_code == 403


def test_list_users_tenant_isolated(auth_client, auth_client_b, admin_b):
    r = auth_client.get("/api/v1/users/")
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert "admin-b@test.com" not in emails


def test_update_user_role(auth_client, regular_user):
    r = auth_client.patch(f"/api/v1/users/{regular_user.id}", json={"role": "admin"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_update_user_requires_admin(user_client, admin_user):
    r = user_client.patch(f"/api/v1/users/{admin_user.id}", json={"role": "viewer"})
    assert r.status_code == 403


def test_deactivate_user(auth_client, regular_user):
    r = auth_client.patch(f"/api/v1/users/{regular_user.id}", json={"is_active": False})
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_cannot_deactivate_self(auth_client, admin_user):
    r = auth_client.patch(f"/api/v1/users/{admin_user.id}", json={"is_active": False})
    assert r.status_code == 400


def test_update_user_wrong_tenant(auth_client, auth_client_b, admin_b):
    r = auth_client.patch(f"/api/v1/users/{admin_b.id}", json={"role": "viewer"})
    assert r.status_code == 404


def test_user_management_web_page(auth_client):
    r = auth_client.get("/users")
    assert r.status_code == 200
    assert b"user@test.com" not in r.content or b"admin@test.com" in r.content
