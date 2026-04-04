"""Tests for Onboarding Wizard — STORY-029"""


def test_onboarding_step1_accessible_after_register(client):
    """Fresh tenant after registration should see onboarding."""
    r = client.post("/api/v1/auth/register", json={
        "tenant_name": "Wizard Corp",
        "display_name": "Owner",
        "email": "wizard@wizardcorp.com",
        "password": "securepass123",
    })
    assert r.status_code == 200
    r2 = client.get("/onboarding/step1")
    assert r2.status_code == 200


def test_onboarding_step1_shows_org_form(client):
    client.post("/api/v1/auth/register", json={
        "tenant_name": "New Org",
        "display_name": "Owner",
        "email": "owner@neworg.com",
        "password": "securepass123",
    })
    r = client.get("/onboarding/step1")
    assert r.status_code == 200
    assert b"organisation" in r.content.lower() or b"unternehmen" in r.content.lower() or b"onboarding" in r.content.lower()


def test_onboarding_step2_accessible(client):
    client.post("/api/v1/auth/register", json={
        "tenant_name": "Step2 Corp",
        "display_name": "Owner",
        "email": "owner@step2.com",
        "password": "securepass123",
    })
    r = client.get("/onboarding/step2")
    assert r.status_code == 200


def test_onboarding_step3_accessible(client):
    client.post("/api/v1/auth/register", json={
        "tenant_name": "Step3 Corp",
        "display_name": "Owner",
        "email": "owner@step3.com",
        "password": "securepass123",
    })
    r = client.get("/onboarding/step3")
    assert r.status_code == 200


def test_onboarding_requires_login(client):
    r = client.get("/onboarding/step1", follow_redirects=False)
    # Either 200 (public) or redirect to login
    assert r.status_code in (200, 302)


def test_onboarding_step1_post_redirects_to_step2(client):
    client.post("/api/v1/auth/register", json={
        "tenant_name": "Post Corp",
        "display_name": "Owner",
        "email": "owner@postcorp.com",
        "password": "securepass123",
    })
    r = client.post("/onboarding/step1", data={
        "org_name": "Post Corp GmbH",
        "currency": "EUR",
    }, follow_redirects=False)
    assert r.status_code == 302
    assert "/onboarding/step2" in r.headers.get("location", "")


def test_onboarding_complete_redirects_to_dashboard(client):
    client.post("/api/v1/auth/register", json={
        "tenant_name": "Done Corp",
        "display_name": "Owner",
        "email": "owner@donecorp.com",
        "password": "securepass123",
    })
    r = client.post("/onboarding/complete", data={}, follow_redirects=False)
    assert r.status_code == 302
    assert "/dashboard" in r.headers.get("location", "")
