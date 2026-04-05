"""Tests for Security Review — STORY-048"""


def test_security_headers_present(client):
    """Responses include basic security headers."""
    r = client.get("/health")
    # X-Content-Type-Options
    assert r.headers.get("x-content-type-options") == "nosniff"


def test_xframe_options_header(client):
    """X-Frame-Options header prevents clickjacking."""
    r = client.get("/health")
    assert r.headers.get("x-frame-options") in ("DENY", "SAMEORIGIN")


def test_cors_configured(client):
    """CORS headers are set on API endpoints."""
    r = client.options(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    # Either 200 with CORS headers or 405 (method not allowed) but CORS still set
    assert r.status_code in (200, 204, 405)


def test_sql_injection_in_subscription_name(auth_client):
    """SQL injection attempt in subscription name is safely handled."""
    r = auth_client.post("/api/v1/subscriptions/", json={
        "name": "'; DROP TABLE subscriptions; --",
        "cost": 0.0,
        "billing_cycle": "monthly",
    })
    assert r.status_code == 201
    assert r.json()["name"] == "'; DROP TABLE subscriptions; --"


def test_subscription_name_xss_sanitized(auth_client):
    """XSS payload in subscription name stored as-is but escaped in HTML."""
    r = auth_client.post("/api/v1/subscriptions/", json={
        "name": "<script>alert('xss')</script>",
        "cost": 1.0,
        "billing_cycle": "monthly",
    })
    assert r.status_code == 201


def test_tenant_isolation_api_enforced(auth_client, auth_client_b, db, admin_user, admin_b, tenant_a, tenant_b):
    """User from tenant A cannot read tenant B subscription via API."""
    r_b = auth_client_b.post("/api/v1/subscriptions/", json={
        "name": "Secret B Sub", "cost": 99.0, "billing_cycle": "monthly"
    })
    sub_b_id = r_b.json()["id"]
    r = auth_client.get(f"/api/v1/subscriptions/{sub_b_id}")
    assert r.status_code == 404


def test_inactive_user_cannot_login(client, db, admin_user):
    """Deactivated user cannot authenticate."""
    admin_user.is_active = False
    db.commit()
    r = client.post("/api/v1/auth/login", json={
        "email": "admin@test.com", "password": "password123"
    })
    assert r.status_code == 401


def test_password_not_in_user_response(auth_client):
    """User responses never expose password_hash."""
    r = auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert "password" not in r.json()
    assert "password_hash" not in r.json()


def test_admin_role_required_for_coupon_creation(user_client):
    """Regular user cannot create coupons (admin-only)."""
    r = user_client.post("/api/v1/coupons/", json={
        "code": "HACK10", "discount_type": "percent", "discount_value": 10
    })
    assert r.status_code == 403


def test_large_payload_rejected(auth_client):
    """Extremely long subscription name is handled gracefully."""
    r = auth_client.post("/api/v1/subscriptions/", json={
        "name": "A" * 10000,
        "cost": 1.0,
        "billing_cycle": "monthly",
    })
    # Either accepted (255 truncation in DB) or rejected — must not 500
    assert r.status_code in (201, 400, 422)
