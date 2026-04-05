"""Tests for Cashflow Dashboard Web UI — STORY-066."""


def test_cashflow_dashboard_requires_login(client):
    r = client.get("/cashflow", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["location"]


def test_cashflow_dashboard_renders(auth_client):
    r = auth_client.get("/cashflow")
    assert r.status_code == 200
    assert "Cashflow Dashboard" in r.text
    assert "Monatlicher Netto-Cashflow" in r.text


def test_cashflow_dashboard_shows_sections(auth_client):
    r = auth_client.get("/cashflow")
    assert r.status_code == 200
    assert "Einnahmen" in r.text
    assert "Ausgaben" in r.text
    assert "Sparrate" in r.text
    assert "Gesamtverm" in r.text  # Gesamtvermögen (umlaut)


def test_cashflow_dashboard_has_chart(auth_client):
    r = auth_client.get("/cashflow")
    assert r.status_code == 200
    assert "chart.js" in r.text or "Chart" in r.text
    assert "cashflowChart" in r.text


def test_cashflow_nav_link_exists(auth_client):
    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    assert 'href="/cashflow"' in r.text
    assert "Cashflow" in r.text
