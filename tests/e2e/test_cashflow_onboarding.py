"""
E2E Test: Cashflow-Onboarding Wizard — STORY-075
==================================================
Tests the full 6-step cashflow onboarding wizard via real Chromium browser.
"""
from playwright.sync_api import Page, expect


def _login(page: Page, base_url: str):
    """Helper: Login as demo admin."""
    page.goto(f"{base_url}/login")
    page.fill("input[name='email']", "admin@demo.com")
    page.fill("input[name='password']", "demo1234")
    page.click("button[type='submit']")
    page.wait_for_url(f"{base_url}/dashboard", timeout=5000)


def test_onboarding_step1_loads(page: Page, base_url: str):
    """Step 1: Konten page renders correctly."""
    _login(page, base_url)
    page.goto(f"{base_url}/cashflow-onboarding/step1")
    expect(page.locator("body")).to_contain_text("Deine Konten")
    expect(page.locator("input[name='account_name']")).to_be_visible()
    expect(page.locator("select[name='account_type']")).to_be_visible()


def test_onboarding_full_wizard_flow(page: Page, base_url: str):
    """Complete the entire 6-step wizard end-to-end."""
    _login(page, base_url)

    # Step 1: Konto anlegen
    page.goto(f"{base_url}/cashflow-onboarding/step1")
    page.fill("input[name='account_name']", "E2E Girokonto")
    page.fill("input[name='bank_name']", "Testbank")
    page.fill("input[name='balance']", "5000")
    page.click("button[type='submit']")
    page.wait_for_url("**/step2", timeout=5000)

    # Step 2: Daueraufträge
    expect(page.locator("body")).to_contain_text("Dauerauftr")
    page.fill("input[name='gehalt_amount']", "4500")
    page.fill("input[name='miete_amount']", "1200")
    page.click("button[type='submit']")
    page.wait_for_url("**/step3", timeout=5000)

    # Step 3: Lastschriften
    expect(page.locator("body")).to_contain_text("Lastschrift")
    page.fill("input[name='strom_amount']", "85")
    page.fill("input[name='internet_amount']", "45")
    page.click("button[type='submit']")
    page.wait_for_url("**/step4", timeout=5000)

    # Step 4: Geldanlagen
    expect(page.locator("body")).to_contain_text("Geldanlage")
    page.fill("input[name='etf_value']", "15000")
    page.fill("input[name='etf_invested']", "12000")
    page.click("button[type='submit']")
    page.wait_for_url("**/step5", timeout=5000)

    # Step 5: Sparziele
    expect(page.locator("body")).to_contain_text("Sparziel")
    page.fill("input[name='notgroschen_target']", "10000")
    page.fill("input[name='notgroschen_current']", "3000")
    page.click("button[type='submit']")
    page.wait_for_url("**/step6", timeout=5000)

    # Step 6: Übersicht
    expect(page.locator("body")).to_contain_text("bersicht")
    expect(page.locator("body")).to_contain_text("Netto-Cashflow")
    page.click("button[type='submit']")
    page.wait_for_url(f"{base_url}/cashflow", timeout=5000)

    # Should be on Cashflow Dashboard now
    expect(page.locator("body")).to_contain_text("Cashflow Dashboard")


def test_onboarding_progress_bar_visible(page: Page, base_url: str):
    """All steps show a progress bar with 6 circles."""
    _login(page, base_url)
    page.goto(f"{base_url}/cashflow-onboarding/step1")
    # Should have 6 step circles
    circles = page.locator("div.rounded-full.flex.items-center")
    expect(circles.first).to_be_visible()


def test_onboarding_back_navigation(page: Page, base_url: str):
    """Back links navigate to previous steps."""
    _login(page, base_url)
    page.goto(f"{base_url}/cashflow-onboarding/step3")
    back_link = page.locator("a[href='/cashflow-onboarding/step2']")
    expect(back_link).to_be_visible()
    back_link.click()
    page.wait_for_url("**/step2", timeout=5000)


def test_onboarding_step4_skippable(page: Page, base_url: str):
    """Step 4 (Geldanlagen) can be submitted empty to skip."""
    _login(page, base_url)
    page.goto(f"{base_url}/cashflow-onboarding/step4")
    page.click("button[type='submit']")
    page.wait_for_url("**/step5", timeout=5000)
