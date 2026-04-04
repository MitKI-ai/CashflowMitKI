"""Tests for Cashflow Onboarding Wizard — STORY-070 to 074."""


def test_cashflow_onboarding_requires_login(client):
    r = client.get("/cashflow-onboarding/step1", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["location"]


# ── Step 1: Konten ──────────────────────────────────────────────────

def test_step1_renders(auth_client):
    r = auth_client.get("/cashflow-onboarding/step1")
    assert r.status_code == 200
    assert "Deine Konten" in r.text
    assert "step" in r.text.lower() or "Schritt" in r.text


def test_step1_submit_creates_account(auth_client):
    r = auth_client.post("/cashflow-onboarding/step1", data={
        "account_name": "Girokonto",
        "account_type": "checking",
        "bank_name": "Sparkasse",
        "balance": "3200.00",
    }, follow_redirects=False)
    assert r.status_code == 302
    assert "step2" in r.headers["location"]
    # Verify account was created
    accounts = auth_client.get("/api/v1/accounts/").json()
    assert any(a["name"] == "Girokonto" for a in accounts)


# ── Step 2: Daueraufträge ──────────────────────────────────────────

def test_step2_renders(auth_client):
    r = auth_client.get("/cashflow-onboarding/step2")
    assert r.status_code == 200
    assert "Dauerauftr" in r.text  # Daueraufträge


def test_step2_submit_creates_standing_orders(auth_client):
    # First create an account
    auth_client.post("/cashflow-onboarding/step1", data={
        "account_name": "Girokonto", "account_type": "checking",
        "bank_name": "Test", "balance": "1000",
    })
    r = auth_client.post("/cashflow-onboarding/step2", data={
        "gehalt_amount": "4500",
        "miete_amount": "1200",
        "versicherung_amount": "100",
    }, follow_redirects=False)
    assert r.status_code == 302
    assert "step3" in r.headers["location"]


# ── Step 3: Lastschriften ──────────────────────────────────────────

def test_step3_renders(auth_client):
    r = auth_client.get("/cashflow-onboarding/step3")
    assert r.status_code == 200
    assert "Lastschrift" in r.text


def test_step3_submit(auth_client):
    auth_client.post("/cashflow-onboarding/step1", data={
        "account_name": "Konto", "account_type": "checking",
        "bank_name": "Test", "balance": "500",
    })
    r = auth_client.post("/cashflow-onboarding/step3", data={
        "strom_amount": "85",
        "internet_amount": "45",
    }, follow_redirects=False)
    assert r.status_code == 302
    assert "step4" in r.headers["location"]


# ── Step 4: Geldanlagen ──────────────────────────────────────────

def test_step4_renders(auth_client):
    r = auth_client.get("/cashflow-onboarding/step4")
    assert r.status_code == 200
    assert "Geldanlage" in r.text


def test_step4_skip(auth_client):
    r = auth_client.post("/cashflow-onboarding/step4", data={}, follow_redirects=False)
    assert r.status_code == 302
    assert "step5" in r.headers["location"]


# ── Step 5: Sparziele ──────────────────────────────────────────

def test_step5_renders(auth_client):
    r = auth_client.get("/cashflow-onboarding/step5")
    assert r.status_code == 200
    assert "Sparziel" in r.text


def test_step5_submit(auth_client):
    r = auth_client.post("/cashflow-onboarding/step5", data={
        "notgroschen_target": "10000",
        "notgroschen_current": "2000",
        "urlaub_target": "3000",
    }, follow_redirects=False)
    assert r.status_code == 302
    assert "step6" in r.headers["location"]


# ── Step 6: Übersicht + Abschluss ──────────────────────────────

def test_step6_renders(auth_client):
    r = auth_client.get("/cashflow-onboarding/step6")
    assert r.status_code == 200
    assert "bersicht" in r.text  # Übersicht


def test_step6_complete_redirects_to_cashflow(auth_client):
    r = auth_client.post("/cashflow-onboarding/complete", follow_redirects=False)
    assert r.status_code == 302
    assert "/cashflow" in r.headers["location"]


# ── Progress bar ──────────────────────────────────────────────────

def test_all_steps_have_progress_bar(auth_client):
    for step in range(1, 7):
        r = auth_client.get(f"/cashflow-onboarding/step{step}")
        assert r.status_code == 200
        # Check for step indicators (1-6)
        assert "1" in r.text and "6" in r.text
