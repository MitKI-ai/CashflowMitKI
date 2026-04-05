"""Tests for Dashboard Widget System — STORY-083, 084, 085."""
import pytest


# ── Widget Registry ──────────────────────────────────────────────────

def test_list_available_widgets(auth_client):
    r = auth_client.get("/api/v1/widgets/available")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 8
    for w in data:
        assert "id" in w
        assert "title" in w
        assert "type" in w  # kpi, chart, list
        assert "size" in w  # 1x1, 2x1, 2x2


def test_available_widgets_include_standard(auth_client):
    r = auth_client.get("/api/v1/widgets/available")
    widget_ids = [w["id"] for w in r.json()]
    expected = ["net_cashflow", "net_worth", "savings_rate", "next_payments",
                "budget_status", "savings_progress", "monthly_trend", "asset_allocation"]
    for wid in expected:
        assert wid in widget_ids, f"Missing widget: {wid}"


# ── User Widget Config ──────────────────────────────────────────────

def test_get_widget_config_default(auth_client):
    r = auth_client.get("/api/v1/widgets/config")
    assert r.status_code == 200
    data = r.json()
    assert "widgets" in data
    assert len(data["widgets"]) > 0  # default preset


def test_update_widget_config(auth_client):
    r = auth_client.put("/api/v1/widgets/config", json={
        "widgets": ["net_cashflow", "net_worth", "savings_rate"],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["widgets"] == ["net_cashflow", "net_worth", "savings_rate"]


def test_widget_config_persists(auth_client):
    auth_client.put("/api/v1/widgets/config", json={
        "widgets": ["net_cashflow", "budget_status"],
    })
    r = auth_client.get("/api/v1/widgets/config")
    assert r.json()["widgets"] == ["net_cashflow", "budget_status"]


# ── Presets ──────────────────────────────────────────────────────────

def test_list_presets(auth_client):
    r = auth_client.get("/api/v1/widgets/presets")
    assert r.status_code == 200
    data = r.json()
    preset_names = [p["name"] for p in data]
    assert "sparer" in preset_names
    assert "familie" in preset_names
    assert "investor" in preset_names


def test_apply_preset(auth_client):
    r = auth_client.post("/api/v1/widgets/apply-preset", json={"preset": "investor"})
    assert r.status_code == 200
    data = r.json()
    assert "net_worth" in data["widgets"]
    assert "asset_allocation" in data["widgets"]


# ── Widget Data ──────────────────────────────────────────────────────

def test_widget_data_endpoint(auth_client):
    """Each widget can fetch its data."""
    r = auth_client.get("/api/v1/widgets/data/net_cashflow")
    assert r.status_code == 200
    data = r.json()
    assert "value" in data or "data" in data


def test_widget_data_unknown_widget(auth_client):
    r = auth_client.get("/api/v1/widgets/data/nonexistent")
    assert r.status_code == 404


def test_widget_tenant_isolation(auth_client, auth_client_b):
    auth_client.put("/api/v1/widgets/config", json={
        "widgets": ["net_cashflow"],
    })
    r = auth_client_b.get("/api/v1/widgets/config")
    # Tenant B should have default, not tenant A's config
    assert r.json()["widgets"] != ["net_cashflow"] or len(r.json()["widgets"]) > 1
