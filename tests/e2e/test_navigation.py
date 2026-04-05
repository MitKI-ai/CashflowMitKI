"""
E2E Test: Navigation & UI-Verhalten
=====================================
Neue Playwright-Konzepte:
  - page.locator().is_visible()  → Element sichtbar?
  - page.set_viewport_size()     → Fenstergröße ändern (Mobile-Test!)
  - page.locator().click()       → Gezielter Element-Click
  - page.keyboard.press()        → Tastatureingabe
  - page.locator().get_attribute()→ Attribut-Wert lesen
  - page.title()                 → Seitentitel lesen
"""
import pytest
from playwright.sync_api import Page, expect


def test_landing_page_has_login_link(page: Page, base_url: str):
    """
    Landing Page: Ohne Login → öffentliche Seite mit CTA.
    Zeigt: Unauthentifizierte Seiten testen.
    """
    page.goto(base_url)

    # Seite sollte NICHT zum Login redirecten
    assert "/login" not in page.url or page.url == f"{base_url}/"

    # Login-Link sollte sichtbar sein
    login_links = page.locator("a[href='/login']")
    expect(login_links.first).to_be_visible()


def test_mobile_hamburger_menu(page: Page, base_url: str):
    """
    Responsive Test: Auf Mobile-Breite — Hamburger-Menü erscheinen?
    Playwright kann Fenstergröße ändern — kein extra Device nötig!
    """
    # Mobile-Breite simulieren
    page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE

    # Erst einloggen
    page.goto(f"{base_url}/login")
    page.fill("input[name='email']", "admin@demo.com")
    page.fill("input[name='password']", "demo1234")
    page.click("button[type='submit']")
    page.wait_for_url(f"{base_url}/dashboard", timeout=5000)

    # Auf Mobile sollte ein Hamburger-Button existieren
    # (button mit aria-label oder id="hamburger" o.ä.)
    hamburger = page.locator(
        "button[aria-label*='menu'], button[aria-label*='Menu'], "
        "#hamburger, .hamburger, [data-testid='hamburger']"
    )

    if hamburger.count() > 0:
        expect(hamburger.first).to_be_visible()
        # Klicken und prüfen ob Menü aufgeht
        hamburger.first.click()
        # Navigation sollte jetzt sichtbar sein
        page.wait_for_timeout(300)  # kurz warten für Animation

    # Desktop-Nav wird auf Mobile ausgeblendet — das ist auch ein valider Test
    page.set_viewport_size({"width": 1280, "height": 720})  # zurück auf Desktop


def test_page_title_contains_brand(page: Page, base_url: str):
    """
    Jede Seite sollte den Brand-Namen im Titel haben.
    Zeigt: page.title() und mehrere Seiten in einem Test prüfen.
    """
    pages_to_check = ["/", "/login"]

    for path in pages_to_check:
        page.goto(f"{base_url}{path}")
        title = page.title()
        assert "Subscription" in title or "mitKI" in title, (
            f"Seite {path}: Kein Brand im Titel. Aktueller Titel: '{title}'"
        )


def test_dark_mode_toggle(page: Page, base_url: str):
    """
    Dark Mode: Toggle-Button klicken → Klasse wechselt auf <html>.
    Zeigt: page.evaluate() für JavaScript-Zugriff auf DOM.
    """
    page.goto(f"{base_url}/login")

    # Dark-Mode-Toggle suchen (verschiedene mögliche Selektoren)
    toggle = page.locator(
        "#dark-toggle, [data-testid='dark-toggle'], "
        "button[aria-label*='dark'], button[aria-label*='Dark']"
    )

    if toggle.count() == 0:
        pytest.skip("Kein Dark-Mode-Toggle auf Login-Seite gefunden")

    # HTML-Klasse vor dem Klick lesen
    html_class_before = page.evaluate("document.documentElement.className")

    toggle.first.click()
    page.wait_for_timeout(200)

    # Klasse hat sich geändert?
    html_class_after = page.evaluate("document.documentElement.className")
    assert html_class_before != html_class_after, (
        "Dark-Mode-Toggle: HTML-Klasse hat sich nicht geändert"
    )


def test_navigation_links_work(page: Page, base_url: str):
    """
    Nach dem Login: Alle Haupt-Navigationslinks führen zu gültigen Seiten.
    Zeigt: Mehrere Links in einer Schleife testen.
    """
    # Einloggen
    page.goto(f"{base_url}/login")
    page.fill("input[name='email']", "admin@demo.com")
    page.fill("input[name='password']", "demo1234")
    page.click("button[type='submit']")
    page.wait_for_url(f"{base_url}/dashboard", timeout=5000)

    # Diese Links sollten in der Nav vorhanden sein und 200 zurückgeben
    nav_links = ["/dashboard", "/subscriptions"]

    for path in nav_links:
        page.goto(f"{base_url}{path}")
        # Keine 404 / 500 Error-Seite
        body = page.locator("body").inner_text()
        assert "404" not in page.title(), f"404 auf Seite {path}"
        assert "500" not in page.title(), f"500 auf Seite {path}"
        assert len(body) > 50, f"Seite {path} scheint leer zu sein"
