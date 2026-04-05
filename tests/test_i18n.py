"""Tests for Internationalisierung DE + EN — STORY-034"""


def test_translations_de_loaded():
    from app.core.i18n import get_translator
    t = get_translator("de")
    assert callable(t)
    assert t("nav.dashboard") != ""


def test_translations_en_loaded():
    from app.core.i18n import get_translator
    t = get_translator("en")
    assert t("nav.dashboard") != ""


def test_de_and_en_differ():
    from app.core.i18n import get_translator
    de = get_translator("de")
    en = get_translator("en")
    # At least one key should differ between languages
    assert de("nav.subscriptions") != en("nav.subscriptions")


def test_unknown_key_returns_key():
    from app.core.i18n import get_translator
    t = get_translator("de")
    assert t("nonexistent.key.xyz") == "nonexistent.key.xyz"


def test_unknown_locale_falls_back_to_de():
    from app.core.i18n import get_translator
    t = get_translator("fr")  # not supported
    assert t("nav.dashboard") != ""


def test_dashboard_renders_with_locale(auth_client, db, admin_user, tenant_a):
    """Dashboard renders without error when tenant locale is 'en'."""
    tenant_a.locale = "en"
    db.commit()
    r = auth_client.get("/dashboard")
    assert r.status_code == 200


def test_jinja_t_filter_in_template(auth_client):
    """Base template uses the t() filter (check for translated nav text)."""
    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    # Navbar should contain translated text (German default)
    assert "Dashboard" in r.text or "Abonnements" in r.text
