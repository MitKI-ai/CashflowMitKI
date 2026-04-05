"""Tests for STORY-012: Web UI — category badges + category filter on /subscriptions"""
from tests.conftest import make_category, make_subscription


def test_subscriptions_page_shows_category_badge(auth_client, db, admin_user, tenant_a):
    cat = make_category(db, tenant_a.id, name="DevOps", color="#0000FF")
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="GitHub Actions")
    # Assign category via API
    auth_client.put(f"/api/v1/subscriptions/{sub.id}", json={"category_ids": [cat.id]})

    r = auth_client.get("/subscriptions")
    assert r.status_code == 200
    assert "DevOps" in r.text


def test_subscriptions_page_has_category_filter_links(auth_client, db, admin_user, tenant_a):
    cat = make_category(db, tenant_a.id, name="Cloud")
    r = auth_client.get("/subscriptions")
    assert r.status_code == 200
    # Category filter links must include the category id
    assert cat.id in r.text


def test_subscriptions_page_category_filter_returns_matching(auth_client, db, admin_user, tenant_a):
    cat = make_category(db, tenant_a.id, name="SaaS")
    sub_tagged = make_subscription(db, tenant_a.id, admin_user.id, name="Notion")
    sub_untagged = make_subscription(db, tenant_a.id, admin_user.id, name="Excel")
    auth_client.put(f"/api/v1/subscriptions/{sub_tagged.id}", json={"category_ids": [cat.id]})

    r = auth_client.get(f"/subscriptions?category_id={cat.id}")
    assert r.status_code == 200
    assert "Notion" in r.text
    assert "Excel" not in r.text


def test_subscriptions_page_no_category_filter_shows_all(auth_client, db, admin_user, tenant_a):
    make_subscription(db, tenant_a.id, admin_user.id, name="Abo1")
    make_subscription(db, tenant_a.id, admin_user.id, name="Abo2")
    r = auth_client.get("/subscriptions")
    assert r.status_code == 200
    assert "Abo1" in r.text
    assert "Abo2" in r.text
