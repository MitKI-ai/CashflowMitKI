"""Tests for STORY-007: Health + Metrics Endpoints"""


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["database"] == "ok"


def test_health_no_auth_required(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_metrics_structure(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    data = r.json()
    assert "tenants" in data
    assert "users" in data
    assert "subscriptions_total" in data
    assert "subscriptions_active" in data


def test_metrics_counts_reflect_data(client, admin_user, auth_client):
    r = auth_client.get("/metrics")
    data = r.json()
    assert data["tenants"] >= 1
    assert data["users"] >= 1
