"""Tests for STORY-011: Categories CRUD + STORY-012: Category Filter"""


def test_create_category(auth_client):
    r = auth_client.post("/api/v1/categories/", json={"name": "SaaS", "color": "#FF5733"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "SaaS"
    assert data["color"] == "#FF5733"
    assert "id" in data
    assert "tenant_id" in data


def test_create_category_requires_admin(user_client):
    r = user_client.post("/api/v1/categories/", json={"name": "SaaS"})
    assert r.status_code == 403


def test_list_categories(auth_client):
    auth_client.post("/api/v1/categories/", json={"name": "SaaS"})
    auth_client.post("/api/v1/categories/", json={"name": "Cloud"})
    r = auth_client.get("/api/v1/categories/")
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert "SaaS" in names
    assert "Cloud" in names


def test_update_category(auth_client):
    r = auth_client.post("/api/v1/categories/", json={"name": "Old"})
    cat_id = r.json()["id"]
    r = auth_client.put(f"/api/v1/categories/{cat_id}", json={"name": "New", "color": "#000000"})
    assert r.status_code == 200
    assert r.json()["name"] == "New"


def test_delete_category(auth_client):
    r = auth_client.post("/api/v1/categories/", json={"name": "ToDelete"})
    cat_id = r.json()["id"]
    r = auth_client.delete(f"/api/v1/categories/{cat_id}")
    assert r.status_code == 204
    r = auth_client.get("/api/v1/categories/")
    assert all(c["id"] != cat_id for c in r.json())


def test_category_tenant_isolation(auth_client, auth_client_b):
    # Tenant A creates a category
    auth_client.post("/api/v1/categories/", json={"name": "Tenant A Only"})
    # Tenant B sees zero categories
    r = auth_client_b.get("/api/v1/categories/")
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_update_category_wrong_tenant(auth_client, auth_client_b):
    r = auth_client.post("/api/v1/categories/", json={"name": "Mine"})
    cat_id = r.json()["id"]
    r = auth_client_b.put(f"/api/v1/categories/{cat_id}", json={"name": "Stolen"})
    assert r.status_code == 404


# --- STORY-012: Category Filter ---

def test_filter_subscriptions_by_category(auth_client, db, admin_user, tenant_a):
    from tests.conftest import make_category, make_subscription

    cat = make_category(db, tenant_a.id, name="Produktiv")
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="GitHub", status="active")
    # Assign category via API
    auth_client.put(
        f"/api/v1/subscriptions/{sub.id}",
        json={"category_ids": [cat.id]},
    )

    r = auth_client.get(f"/api/v1/subscriptions/?category_id={cat.id}")
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()]
    assert sub.id in ids


def test_filter_subscriptions_by_category_no_match(auth_client, db, admin_user, tenant_a):
    from tests.conftest import make_category, make_subscription

    cat = make_category(db, tenant_a.id, name="Empty Cat")
    make_subscription(db, tenant_a.id, admin_user.id, name="Untagged")

    r = auth_client.get(f"/api/v1/subscriptions/?category_id={cat.id}")
    assert r.status_code == 200
    assert len(r.json()) == 0
