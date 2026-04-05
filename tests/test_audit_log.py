"""Tests for STORY-019: Audit Log — write on CRUD + admin view"""
from tests.conftest import make_subscription


# ── Audit log written on subscription events ─────────────────────────────────

def test_audit_log_on_subscription_create(auth_client, db, tenant_a, admin_user):
    from app.models.audit import AuditLog
    r = auth_client.post("/api/v1/subscriptions/", json={
        "name": "Audit Test", "cost": 9.99, "currency": "EUR",
        "billing_cycle": "monthly", "status": "active",
    })
    assert r.status_code == 201
    log = db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_a.id,
        AuditLog.action == "create",
        AuditLog.entity_type == "subscription",
    ).first()
    assert log is not None
    assert log.user_id == admin_user.id


def test_audit_log_on_subscription_update(auth_client, db, tenant_a, admin_user):
    from app.models.audit import AuditLog
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="Before")
    auth_client.put(f"/api/v1/subscriptions/{sub.id}", json={"name": "After"})
    log = db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_a.id,
        AuditLog.action == "update",
        AuditLog.entity_id == sub.id,
    ).first()
    assert log is not None


def test_audit_log_on_subscription_delete(auth_client, db, tenant_a, admin_user):
    from app.models.audit import AuditLog
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="Delete Me")
    sub_id = sub.id
    auth_client.delete(f"/api/v1/subscriptions/{sub_id}")
    log = db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_a.id,
        AuditLog.action == "delete",
        AuditLog.entity_id == sub_id,
    ).first()
    assert log is not None


# ── Admin view ────────────────────────────────────────────────────────────────

def test_audit_log_api_returns_list(auth_client, db, tenant_a, admin_user):
    make_subscription(db, tenant_a.id, admin_user.id, name="Trigger")
    auth_client.post("/api/v1/subscriptions/", json={
        "name": "Log Me", "cost": 5.0, "currency": "EUR",
        "billing_cycle": "monthly", "status": "active",
    })
    r = auth_client.get("/api/v1/audit/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_audit_log_api_admin_only(user_client):
    r = user_client.get("/api/v1/audit/")
    assert r.status_code == 403


def test_audit_log_tenant_isolated(auth_client, auth_client_b, db, tenant_a, admin_user):
    auth_client.post("/api/v1/subscriptions/", json={
        "name": "Tenant A Sub", "cost": 1.0, "currency": "EUR",
        "billing_cycle": "monthly", "status": "active",
    })
    r = auth_client_b.get("/api/v1/audit/")
    assert r.status_code == 200
    entries = r.json()
    # Tenant B should see zero entries (nothing created for them)
    assert len(entries) == 0


def test_audit_log_web_page_accessible(auth_client):
    r = auth_client.get("/audit")
    assert r.status_code == 200
    assert "Audit" in r.text
