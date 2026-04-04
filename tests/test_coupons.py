"""Tests for Coupons + Rabattcodes — STORY-038"""
from datetime import datetime, timedelta, timezone


def _coupon(**kwargs):
    defaults = {
        "code": "SAVE10",
        "discount_type": "percent",
        "discount_value": 10.0,
        "max_uses": 100,
    }
    defaults.update(kwargs)
    return defaults


def test_create_coupon(auth_client):
    r = auth_client.post("/api/v1/coupons/", json=_coupon())
    assert r.status_code == 201
    data = r.json()
    assert data["code"] == "SAVE10"
    assert data["discount_value"] == 10.0


def test_create_coupon_requires_admin(user_client):
    r = user_client.post("/api/v1/coupons/", json=_coupon())
    assert r.status_code == 403


def test_create_duplicate_coupon_code_rejected(auth_client):
    auth_client.post("/api/v1/coupons/", json=_coupon(code="UNIQUE"))
    r = auth_client.post("/api/v1/coupons/", json=_coupon(code="UNIQUE"))
    assert r.status_code == 409


def test_list_coupons(auth_client):
    auth_client.post("/api/v1/coupons/", json=_coupon(code="A10"))
    auth_client.post("/api/v1/coupons/", json=_coupon(code="B20"))
    r = auth_client.get("/api/v1/coupons/")
    assert r.status_code == 200
    codes = [c["code"] for c in r.json()]
    assert "A10" in codes and "B20" in codes


def test_delete_coupon(auth_client):
    r = auth_client.post("/api/v1/coupons/", json=_coupon(code="DEL"))
    cid = r.json()["id"]
    r2 = auth_client.delete(f"/api/v1/coupons/{cid}")
    assert r2.status_code == 200


def test_coupon_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/coupons/", json=_coupon(code="TENA"))
    r = auth_client_b.get("/api/v1/coupons/")
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_validate_valid_coupon(auth_client):
    auth_client.post("/api/v1/coupons/", json=_coupon(code="VALID20"))
    r = auth_client.get("/api/v1/coupons/validate?code=VALID20")
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert data["discount_type"] == "percent"
    assert data["discount_value"] == 10.0


def test_validate_unknown_coupon_returns_invalid(auth_client):
    r = auth_client.get("/api/v1/coupons/validate?code=NOTEXIST")
    assert r.status_code == 200
    assert r.json()["valid"] is False


def test_validate_expired_coupon_returns_invalid(auth_client, db, admin_user, tenant_a):
    from app.models.coupon import Coupon
    c = Coupon(
        tenant_id=tenant_a.id,
        code="EXPIRED",
        discount_type="percent",
        discount_value=5.0,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(c)
    db.commit()
    r = auth_client.get("/api/v1/coupons/validate?code=EXPIRED")
    assert r.json()["valid"] is False


def test_apply_coupon_percent_discount(auth_client, db, admin_user, tenant_a):
    """Applying a 10% coupon reduces cost by 10%."""
    from tests.conftest import make_subscription
    sub = make_subscription(db, tenant_a.id, admin_user.id, cost=100.0)
    auth_client.post("/api/v1/coupons/", json=_coupon(code="DISC10", discount_type="percent", discount_value=10))
    r = auth_client.post(f"/api/v1/coupons/apply", json={"code": "DISC10", "subscription_id": sub.id})
    assert r.status_code == 200
    assert abs(r.json()["new_cost"] - 90.0) < 0.01


def test_apply_coupon_fixed_discount(auth_client, db, admin_user, tenant_a):
    from tests.conftest import make_subscription
    sub = make_subscription(db, tenant_a.id, admin_user.id, cost=50.0)
    auth_client.post("/api/v1/coupons/", json=_coupon(code="FIXED5", discount_type="fixed", discount_value=5))
    r = auth_client.post("/api/v1/coupons/apply", json={"code": "FIXED5", "subscription_id": sub.id})
    assert r.status_code == 200
    assert abs(r.json()["new_cost"] - 45.0) < 0.01
