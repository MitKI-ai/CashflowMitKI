"""Tests for Team Invitations — STORY-026"""
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

# ── Create invitation ──────────────────────────────────────────────────────────

def test_create_invitation(auth_client):
    r = auth_client.post("/api/v1/invitations/", json={
        "email": "newmember@test.com", "role": "user"
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "newmember@test.com"
    assert data["status"] == "pending"
    assert "token" not in data  # token must not leak in response


def test_create_invitation_requires_admin(user_client):
    r = user_client.post("/api/v1/invitations/", json={
        "email": "x@test.com", "role": "user"
    })
    assert r.status_code == 403


def test_create_invitation_sends_email(auth_client):
    with patch("app.api.v1.invitations.EmailService.send_invitation", return_value=True) as mock_send:
        r = auth_client.post("/api/v1/invitations/", json={
            "email": "invited@test.com", "role": "user"
        })
    assert r.status_code == 201
    mock_send.assert_called_once()
    assert mock_send.call_args.kwargs.get("to") == "invited@test.com"


def test_create_invitation_duplicate_pending(auth_client):
    """Second invite to same email returns 409 if one is still pending."""
    auth_client.post("/api/v1/invitations/", json={"email": "dup@test.com", "role": "user"})
    r = auth_client.post("/api/v1/invitations/", json={"email": "dup@test.com", "role": "user"})
    assert r.status_code == 409


# ── List invitations ──────────────────────────────────────────────────────────

def test_list_invitations(auth_client):
    auth_client.post("/api/v1/invitations/", json={"email": "a@test.com", "role": "user"})
    auth_client.post("/api/v1/invitations/", json={"email": "b@test.com", "role": "admin"})
    r = auth_client.get("/api/v1/invitations/")
    assert r.status_code == 200
    emails = [i["email"] for i in r.json()]
    assert "a@test.com" in emails and "b@test.com" in emails


def test_list_invitations_tenant_isolated(auth_client, auth_client_b):
    auth_client.post("/api/v1/invitations/", json={"email": "tenant-a@test.com", "role": "user"})
    r = auth_client_b.get("/api/v1/invitations/")
    assert r.status_code == 200
    assert len(r.json()) == 0


# ── Accept invitation ──────────────────────────────────────────────────────────

def test_accept_invitation_creates_user(client, db, admin_user, tenant_a):
    import secrets

    from app.models.invitation import Invitation
    token = secrets.token_urlsafe(32)
    inv = Invitation(
        tenant_id=tenant_a.id,
        invited_by_id=admin_user.id,
        email="accept@test.com",
        role="user",
        token=token,
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(inv)
    db.commit()

    r = client.post("/api/v1/invitations/accept", json={
        "token": token,
        "display_name": "New Member",
        "password": "securepass123",
    })
    assert r.status_code == 200
    data = r.json()
    assert "user_id" in data


def test_accept_invitation_marks_accepted(client, db, admin_user, tenant_a):
    import secrets

    from app.models.invitation import Invitation
    token = secrets.token_urlsafe(32)
    inv = Invitation(
        tenant_id=tenant_a.id,
        invited_by_id=admin_user.id,
        email="mark@test.com",
        role="user",
        token=token,
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(inv)
    db.commit()

    client.post("/api/v1/invitations/accept", json={
        "token": token, "display_name": "X", "password": "pass123"
    })
    db.refresh(inv)
    assert inv.status == "accepted"


def test_accept_expired_invitation_returns_410(client, db, admin_user, tenant_a):
    import secrets

    from app.models.invitation import Invitation
    token = secrets.token_urlsafe(32)
    inv = Invitation(
        tenant_id=tenant_a.id,
        invited_by_id=admin_user.id,
        email="expired@test.com",
        role="user",
        token=token,
        status="pending",
        expires_at=datetime.now(UTC) - timedelta(days=1),  # already expired
    )
    db.add(inv)
    db.commit()

    r = client.post("/api/v1/invitations/accept", json={
        "token": token, "display_name": "X", "password": "pass123"
    })
    assert r.status_code == 410


def test_accept_invalid_token_returns_404(client):
    r = client.post("/api/v1/invitations/accept", json={
        "token": "invalid-token", "display_name": "X", "password": "pass"
    })
    assert r.status_code == 404


# ── Revoke invitation ──────────────────────────────────────────────────────────

def test_revoke_invitation(auth_client):
    r = auth_client.post("/api/v1/invitations/", json={"email": "rev@test.com", "role": "user"})
    inv_id = r.json()["id"]
    r2 = auth_client.delete(f"/api/v1/invitations/{inv_id}")
    assert r2.status_code == 200
    r3 = auth_client.get("/api/v1/invitations/")
    statuses = [i["status"] for i in r3.json() if i["id"] == inv_id]
    assert statuses == ["revoked"]
