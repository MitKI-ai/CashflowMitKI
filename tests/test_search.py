"""Tests for FTS5 Volltextsuche — STORY-031"""
from tests.conftest import make_subscription


def test_search_finds_by_name(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, name="Netflix Premium")
    make_subscription(db, tenant_a.id, admin_user.id, name="Spotify Music")
    r = auth_client.get("/api/v1/search?q=netflix")
    assert r.status_code == 200
    results = r.json()
    assert any("Netflix" in s["name"] for s in results)
    assert not any("Spotify" in s["name"] for s in results)


def test_search_finds_by_provider(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, name="Cloud Storage", provider="Amazon AWS")
    r = auth_client.get("/api/v1/search?q=amazon")
    assert r.status_code == 200
    assert any("Amazon" in s["provider"] for s in r.json())


def test_search_finds_by_notes(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, name="Dev Tools", notes="JetBrains IDE Lizenz")
    r = auth_client.get("/api/v1/search?q=jetbrains")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_search_tenant_isolation(auth_client, auth_client_b, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, name="SecretService")
    r = auth_client_b.get("/api/v1/search?q=secretservice")
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_search_empty_query_returns_all(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, name="A")
    make_subscription(db, tenant_a.id, admin_user.id, name="B")
    r = auth_client.get("/api/v1/search?q=")
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_search_requires_auth(client):
    r = client.get("/api/v1/search?q=test")
    assert r.status_code == 401


def test_search_web_page(auth_client):
    r = auth_client.get("/search?q=test")
    assert r.status_code == 200
    assert b"search" in r.content.lower() or b"suche" in r.content.lower()
