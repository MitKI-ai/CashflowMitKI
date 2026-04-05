"""
E2E Test: Login-Flow
=====================
Zeigt die wichtigsten Playwright-Konzepte:
  - page.goto()         → URL aufrufen
  - page.fill()         → Eingabefeld befüllen
  - page.click()        → Button klicken
  - page.wait_for_url() → warten bis URL sich ändert
  - page.locator()      → Element finden
  - expect(locator)     → Assertions über sichtbare Elemente
  - page.screenshot()   → Screenshot speichern
"""
import pytest
from playwright.sync_api import Page, expect


def test_login_page_loads(page: Page, base_url: str):
    """
    Schritt 1: Kann Playwright die Login-Seite öffnen?
    Playwright öffnet Chromium, navigiert zur URL, prüft den Seitentitel.
    """
    page.goto(f"{base_url}/login")

    # Seiteninhalt prüfen — expect() ist Playwright's Assertion-System
    # Es wartet automatisch bis zu 5 Sekunden (auto-waiting)
    expect(page.locator("h1, h2")).to_be_visible()
    expect(page.locator("input[name='email']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()


def test_login_with_wrong_password(page: Page, base_url: str):
    """
    Schritt 2: Was passiert bei falschem Passwort?
    Playwright füllt Formular aus und prüft Fehlermeldung.
    """
    page.goto(f"{base_url}/login")

    # Felder befüllen — Playwright findet das Element, tippt Text ein
    page.fill("input[name='email']", "admin@demo.com")
    page.fill("input[name='password']", "FALSCHES_PASSWORT")

    # Submit-Button klicken
    page.click("button[type='submit']")

    # Fehlermeldung sollte erscheinen (Flash-Message oder Inline-Error)
    # Wir prüfen ob wir NOCH auf /login sind (kein Redirect)
    expect(page).to_have_url(f"{base_url}/login")


def test_successful_login_redirects_to_dashboard(page: Page, base_url: str):
    """
    Schritt 3: Erfolgreicher Login → Redirect zum Dashboard.
    Das ist der wichtigste Happy-Path-Test.
    """
    page.goto(f"{base_url}/login")

    # Demo-Credentials aus conftest.py seed
    page.fill("input[name='email']", "admin@demo.com")
    page.fill("input[name='password']", "demo1234")

    page.click("button[type='submit']")

    # Nach Login: URL sollte sich zu /dashboard ändern
    # wait_for_url() wartet bis zu 5 Sekunden
    page.wait_for_url(f"{base_url}/dashboard", timeout=5000)

    # Dashboard-Inhalt prüfen
    expect(page.locator("body")).to_contain_text("Dashboard")


def test_logout_redirects_to_login(page: Page, base_url: str):
    """
    Schritt 4: Nach dem Logout → zurück zur Login-Seite.
    Zeigt wie man mehrstufige Flows testet.
    """
    # Erst einloggen
    page.goto(f"{base_url}/login")
    page.fill("input[name='email']", "admin@demo.com")
    page.fill("input[name='password']", "demo1234")
    page.click("button[type='submit']")
    page.wait_for_url(f"{base_url}/dashboard", timeout=5000)

    # Jetzt ausloggen — Logout-Link finden und klicken
    # Wir versuchen verschiedene Selektoren (Desktop-Nav oder Mobile-Nav)
    logout_link = page.locator("a[href='/logout']").first
    logout_link.click()

    # Nach Logout: zurück auf Login oder Landing Page
    page.wait_for_url(lambda url: "/login" in url or url == f"{base_url}/", timeout=5000)


def test_screenshot_on_login_page(page: Page, base_url: str, tmp_path):
    """
    Bonus: Screenshot speichern — nützlich für Debugging und Dokumentation.
    Screenshots werden in tmp_path gespeichert (von pytest verwaltet).
    """
    page.goto(f"{base_url}/login")

    # Screenshot der ganzen Seite
    screenshot_path = tmp_path / "login_page.png"
    page.screenshot(path=str(screenshot_path), full_page=True)

    assert screenshot_path.exists()
    print(f"\nScreenshot gespeichert: {screenshot_path}")
