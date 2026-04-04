"""Tests for Cashflow Monthly Calendar — STORY-076."""
import pytest


def test_calendar_api_returns_days(auth_client):
    """Calendar API returns daily entries for a given month."""
    r = auth_client.get("/api/v1/cashflow/calendar?month=2026-03")
    assert r.status_code == 200
    data = r.json()
    assert "days" in data
    assert len(data["days"]) == 31  # March has 31 days


def test_calendar_february(auth_client):
    r = auth_client.get("/api/v1/cashflow/calendar?month=2026-02")
    assert r.status_code == 200
    assert len(r.json()["days"]) == 28


def test_calendar_shows_standing_orders_on_execution_day(auth_client):
    """Standing orders appear on their execution day."""
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Konto", "type": "checking", "bank_name": "Test",
    }).json()
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Gehalt", "type": "income", "amount": 4500.0,
        "frequency": "monthly", "execution_day": 27, "account_id": acc["id"],
    })
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Miete", "type": "expense", "amount": 1200.0,
        "frequency": "monthly", "execution_day": 1, "account_id": acc["id"],
    })

    r = auth_client.get("/api/v1/cashflow/calendar?month=2026-03")
    days = r.json()["days"]

    # Day 1 (index 0) should have Miete
    day1_names = [e["name"] for e in days[0]["entries"]]
    assert "Miete" in day1_names

    # Day 27 (index 26) should have Gehalt
    day27_names = [e["name"] for e in days[26]["entries"]]
    assert "Gehalt" in day27_names


def test_calendar_shows_direct_debits(auth_client):
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Konto", "type": "checking", "bank_name": "Test",
    }).json()
    auth_client.post("/api/v1/direct-debits/", json={
        "name": "Strom", "amount": 85.0, "frequency": "monthly",
        "expected_day": 5, "account_id": acc["id"],
    })

    r = auth_client.get("/api/v1/cashflow/calendar?month=2026-03")
    day5_names = [e["name"] for e in r.json()["days"][4]["entries"]]
    assert "Strom" in day5_names


def test_calendar_running_balance(auth_client):
    """Each day has a running balance."""
    r = auth_client.get("/api/v1/cashflow/calendar?month=2026-03")
    days = r.json()["days"]
    for day in days:
        assert "running_balance" in day


def test_calendar_missing_month_returns_422(auth_client):
    r = auth_client.get("/api/v1/cashflow/calendar")
    assert r.status_code == 422


def test_calendar_web_page_renders(auth_client):
    r = auth_client.get("/cashflow/calendar?month=2026-03")
    assert r.status_code == 200
    assert "Kalender" in r.text or "kalender" in r.text.lower()


def test_calendar_tenant_isolation(auth_client, auth_client_b):
    acc = auth_client.post("/api/v1/accounts/", json={
        "name": "Konto A", "type": "checking", "bank_name": "BankA",
    }).json()
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Geheimes Gehalt", "type": "income", "amount": 9999.0,
        "frequency": "monthly", "execution_day": 15, "account_id": acc["id"],
    })
    r = auth_client_b.get("/api/v1/cashflow/calendar?month=2026-03")
    all_names = []
    for day in r.json()["days"]:
        all_names.extend(e["name"] for e in day["entries"])
    assert "Geheimes Gehalt" not in all_names
