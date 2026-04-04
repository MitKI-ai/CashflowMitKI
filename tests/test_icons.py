"""Tests for Icon Bibliothek — STORY-035"""


def test_icon_list_endpoint(auth_client):
    r = auth_client.get("/api/v1/icons/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_icon_list_has_required_fields(auth_client):
    r = auth_client.get("/api/v1/icons/")
    icons = r.json()
    for icon in icons[:5]:
        assert "id" in icon
        assert "name" in icon
        assert "svg" in icon or "url" in icon


def test_icon_list_no_auth_required(client):
    """Icons are public — no auth needed for the picker."""
    r = client.get("/api/v1/icons/")
    assert r.status_code == 200


def test_icon_search(auth_client):
    r = auth_client.get("/api/v1/icons/?q=netflix")
    assert r.status_code == 200
    results = r.json()
    assert any("netflix" in i["name"].lower() for i in results)


def test_subscription_form_has_icon_picker(auth_client):
    r = auth_client.get("/subscriptions/new")
    assert r.status_code == 200
    assert b"icon" in r.content.lower()


def test_create_subscription_with_icon(auth_client):
    r = auth_client.post("/api/v1/subscriptions/", json={
        "name": "Netflix",
        "cost": 9.99,
        "currency": "EUR",
        "billing_cycle": "monthly",
        "icon_id": "netflix",
    })
    assert r.status_code == 201
    assert r.json()["icon_id"] == "netflix"
