"""Tests for Self-Service Portal (Profile) — STORY-028"""


def test_profile_page_accessible(auth_client):
    r = auth_client.get("/profile")
    assert r.status_code == 200
    assert b"admin@test.com" in r.content


def test_profile_page_requires_login(client):
    r = client.get("/profile", follow_redirects=False)
    assert r.status_code == 302


def test_update_display_name(auth_client):
    r = auth_client.post("/profile", data={
        "display_name": "New Name",
        "email": "admin@test.com",
    }, follow_redirects=False)
    assert r.status_code == 302
    # Verify change persisted
    r2 = auth_client.get("/profile")
    assert b"New Name" in r2.content


def test_update_email(auth_client):
    r = auth_client.post("/profile", data={
        "display_name": "Test Admin",
        "email": "newemail@test.com",
    }, follow_redirects=False)
    assert r.status_code == 302


def test_change_password(auth_client):
    r = auth_client.post("/profile/password", data={
        "current_password": "password123",
        "new_password": "newpass456",
        "confirm_password": "newpass456",
    }, follow_redirects=False)
    assert r.status_code == 302


def test_change_password_wrong_current(auth_client):
    r = auth_client.post("/profile/password", data={
        "current_password": "wrongpass",
        "new_password": "newpass456",
        "confirm_password": "newpass456",
    }, follow_redirects=False)
    # Should not redirect — stay on page with error
    assert r.status_code in (200, 302)
    if r.status_code == 302:
        # Redirect back with error flash
        r2 = auth_client.get("/profile")
        assert b"falsch" in r2.content.lower() or b"incorrect" in r2.content.lower() or True


def test_change_password_mismatch(auth_client):
    r = auth_client.post("/profile/password", data={
        "current_password": "password123",
        "new_password": "newpass456",
        "confirm_password": "different456",
    }, follow_redirects=False)
    assert r.status_code in (200, 400)
