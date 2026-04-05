"""
E2E Test: Bank Import + Settings Flow — STORY-102
===================================================
"""
from playwright.sync_api import Page, expect


def _login(page: Page, base_url: str):
    page.goto(f"{base_url}/login")
    page.fill("input[name='email']", "admin@demo.com")
    page.fill("input[name='password']", "demo1234")
    page.click("button[type='submit']")
    page.wait_for_url(f"{base_url}/dashboard", timeout=5000)


def test_settings_page_has_llm_section(page: Page, base_url: str):
    """Settings page shows LLM provider configuration."""
    _login(page, base_url)
    page.goto(f"{base_url}/settings")
    expect(page.locator("body")).to_contain_text("LLM")
    expect(page.locator("#llm-provider")).to_be_visible()
    expect(page.locator("#llm-api-key")).to_be_visible()


def test_cashflow_dashboard_accessible(page: Page, base_url: str):
    """Cashflow dashboard loads after login."""
    _login(page, base_url)
    page.goto(f"{base_url}/cashflow")
    expect(page.locator("body")).to_contain_text("Cashflow Dashboard")


def test_cashflow_calendar_accessible(page: Page, base_url: str):
    _login(page, base_url)
    page.goto(f"{base_url}/cashflow/calendar?month=2026-03")
    expect(page.locator("body")).to_contain_text("Kalender")


def test_cashflow_simulator_accessible(page: Page, base_url: str):
    _login(page, base_url)
    page.goto(f"{base_url}/cashflow/simulator")
    expect(page.locator("body")).to_contain_text("Simulator")
    expect(page.locator("#income-slider")).to_be_visible()
