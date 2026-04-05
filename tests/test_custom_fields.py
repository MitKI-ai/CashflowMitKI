"""Tests for Custom Fields — STORY-039"""


def test_create_custom_field_schema(auth_client):
    """Admin can define a custom field for their tenant."""
    r = auth_client.post("/api/v1/custom-fields/", json={
        "name": "Vertragsnummer",
        "field_type": "text",
        "required": False,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Vertragsnummer"
    assert data["field_type"] == "text"


def test_create_custom_field_requires_admin(user_client):
    r = user_client.post("/api/v1/custom-fields/", json={"name": "X", "field_type": "text"})
    assert r.status_code == 403


def test_list_custom_fields(auth_client):
    auth_client.post("/api/v1/custom-fields/", json={"name": "Field A", "field_type": "text"})
    auth_client.post("/api/v1/custom-fields/", json={"name": "Field B", "field_type": "number"})
    r = auth_client.get("/api/v1/custom-fields/")
    assert r.status_code == 200
    names = [f["name"] for f in r.json()]
    assert "Field A" in names and "Field B" in names


def test_delete_custom_field(auth_client):
    r = auth_client.post("/api/v1/custom-fields/", json={"name": "Del", "field_type": "text"})
    fid = r.json()["id"]
    r2 = auth_client.delete(f"/api/v1/custom-fields/{fid}")
    assert r2.status_code == 200


def test_custom_field_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/custom-fields/", json={"name": "Secret", "field_type": "text"})
    r = auth_client_b.get("/api/v1/custom-fields/")
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_subscription_stores_custom_field_values(auth_client):
    """Creating a subscription with custom_fields_json stores the data."""
    r = auth_client.post("/api/v1/subscriptions/", json={
        "name": "Custom Sub",
        "cost": 5.0,
        "billing_cycle": "monthly",
        "custom_fields": {"Vertragsnummer": "12345", "Notiz": "VIP"},
    })
    assert r.status_code == 201
    data = r.json()
    assert "custom_fields" in data
    assert data["custom_fields"].get("Vertragsnummer") == "12345"


def test_custom_fields_in_subscription_response(auth_client, db, admin_user, tenant_a):
    import json as _json

    from tests.conftest import make_subscription
    sub = make_subscription(db, tenant_a.id, admin_user.id,
                            name="Has Fields",
                            custom_fields_json=_json.dumps({"key": "value"}))
    r = auth_client.get(f"/api/v1/subscriptions/{sub.id}")
    assert r.status_code == 200
    data = r.json()
    assert "custom_fields" in data
    assert data["custom_fields"].get("key") == "value"
