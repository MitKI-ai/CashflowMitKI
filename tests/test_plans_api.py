"""Tests for Plans API"""


def _plan_payload(**kwargs):
    defaults = {"name": "Basic Plan", "price": 9.99, "currency": "EUR",
                "billing_cycle": "monthly", "is_active": True}
    defaults.update(kwargs)
    return defaults


def test_create_plan(auth_client):
    r = auth_client.post("/api/v1/plans/", json=_plan_payload())
    assert r.status_code == 201
    assert r.json()["name"] == "Basic Plan"


def test_create_plan_requires_admin(user_client):
    r = user_client.post("/api/v1/plans/", json=_plan_payload())
    assert r.status_code == 403


def test_list_plans(auth_client):
    auth_client.post("/api/v1/plans/", json=_plan_payload(name="P1"))
    auth_client.post("/api/v1/plans/", json=_plan_payload(name="P2"))
    r = auth_client.get("/api/v1/plans/")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert "P1" in names and "P2" in names


def test_update_plan(auth_client):
    r = auth_client.post("/api/v1/plans/", json=_plan_payload(name="Old"))
    plan_id = r.json()["id"]
    r2 = auth_client.put(f"/api/v1/plans/{plan_id}", json={"name": "New", "price": 19.99})
    assert r2.status_code == 200
    assert r2.json()["name"] == "New"


def test_delete_plan(auth_client):
    r = auth_client.post("/api/v1/plans/", json=_plan_payload(name="Delete Me"))
    plan_id = r.json()["id"]
    r2 = auth_client.delete(f"/api/v1/plans/{plan_id}")
    assert r2.status_code == 200
    r3 = auth_client.get("/api/v1/plans/")
    assert all(p["id"] != plan_id for p in r3.json())


def test_plan_tenant_isolation(auth_client, auth_client_b):
    auth_client.post("/api/v1/plans/", json=_plan_payload(name="Tenant A Plan"))
    r = auth_client_b.get("/api/v1/plans/")
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_update_plan_wrong_tenant(auth_client, auth_client_b):
    r = auth_client.post("/api/v1/plans/", json=_plan_payload())
    plan_id = r.json()["id"]
    r2 = auth_client_b.put(f"/api/v1/plans/{plan_id}", json={"name": "Stolen"})
    assert r2.status_code == 404
