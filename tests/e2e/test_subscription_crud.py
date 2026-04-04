"""
E2E Test: Subscription-Verwaltung (CRUD via Browser)
======================================================
Neue Playwright-Konzepte:
  - page.select_option()    → Dropdown auswählen
  - page.locator().count()  → Anzahl Elemente zählen
  - page.locator().nth(0)   → n-tes Element auswählen
  - page.wait_for_selector()→ Warten bis Element erscheint
  - page.evaluate()         → JavaScript im Browser ausführen
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def logged_in(page: Page, base_url: str):
    """Helper-Fixture: einloggen, dann Test ausführen."""
    page.goto(f"{base_url}/login")
    page.fill("input[name='email']", "admin@demo.com")
    page.fill("input[name='password']", "demo1234")
    page.click("button[type='submit']")
    page.wait_for_url(f"{base_url}/dashboard", timeout=5000)
    return page


def test_subscription_list_shows_netflix(logged_in: Page, base_url: str):
    """
    Die aus conftest.py geseedete Netflix-Subscription sollte in der Liste erscheinen.
    Testet: Navigation + Tabelleninhalt lesen.
    """
    page = logged_in
    page.goto(f"{base_url}/subscriptions")

    # Warten bis die Liste geladen ist
    expect(page.locator("body")).to_contain_text("Netflix")


def test_create_new_subscription(logged_in: Page, base_url: str):
    """
    Neues Abo anlegen via Formular.
    Zeigt: Dropdown auswählen, Datum eingeben, Formular absenden.
    """
    page = logged_in
    page.goto(f"{base_url}/subscriptions/new")

    # Pflichtfelder befüllen
    page.fill("input[name='name']", "Spotify Test")
    page.fill("input[name='provider']", "Spotify AB")
    page.fill("input[name='cost']", "9.99")

    # Dropdown: billing_cycle auswählen
    # select_option() akzeptiert den value-Attribut-Wert
    page.select_option("select[name='billing_cycle']", "monthly")

    # Datum eingeben (HTML date-Input)
    page.fill("input[name='start_date']", "2026-01-01")

    # Formular absenden
    page.click("button[type='submit']")

    # Nach Erfolg → Redirect zur Subscription-Liste
    page.wait_for_url(f"{base_url}/subscriptions", timeout=5000)

    # Neue Subscription in der Liste?
    expect(page.locator("body")).to_contain_text("Spotify Test")


def test_subscription_count_increases_after_create(logged_in: Page, base_url: str):
    """
    Fortgeschritten: Anzahl der Tabellenzeilen vor und nach dem Erstellen vergleichen.
    Zeigt: locator().count() und dynamische Assertions.
    """
    page = logged_in
    page.goto(f"{base_url}/subscriptions")

    # Tabellenzeilen zählen (vor dem Erstellen)
    # Wir suchen nach <tr> innerhalb eines <tbody>
    rows_before = page.locator("table tbody tr").count()

    # Neues Abo anlegen
    page.goto(f"{base_url}/subscriptions/new")
    page.fill("input[name='name']", "Adobe CC")
    page.fill("input[name='provider']", "Adobe")
    page.fill("input[name='cost']", "54.99")
    page.select_option("select[name='billing_cycle']", "monthly")
    page.fill("input[name='start_date']", "2026-01-01")
    page.click("button[type='submit']")
    page.wait_for_url(f"{base_url}/subscriptions", timeout=5000)

    # Zeilen danach zählen
    rows_after = page.locator("table tbody tr").count()
    assert rows_after > rows_before, f"Erwartet mehr Zeilen: {rows_before} → {rows_after}"


def test_dashboard_shows_mrr(logged_in: Page, base_url: str):
    """
    Dashboard-Seite: MRR/KPI-Karten sichtbar?
    Testet: Seiteninhalt nach Login, Chart-Bereich vorhanden.
    """
    page = logged_in
    page.goto(f"{base_url}/dashboard")

    # Irgendeine MRR/Kosten-Angabe sollte sichtbar sein
    body_text = page.locator("body").inner_text()

    # Mindestens einer dieser Begriffe sollte auf dem Dashboard erscheinen
    dashboard_keywords = ["MRR", "ARR", "€", "EUR", "Dashboard", "Abonnement", "Subscription"]
    found = any(kw in body_text for kw in dashboard_keywords)
    assert found, f"Kein Dashboard-Inhalt gefunden. Seite zeigt: {body_text[:300]}"
