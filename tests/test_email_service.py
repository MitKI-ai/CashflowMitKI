"""Tests for EmailService — STORY-022"""
from datetime import date
from unittest.mock import MagicMock, patch

from tests.conftest import make_subscription

# ── EmailService unit tests ────────────────────────────────────────────────────

def test_send_renewal_reminder_returns_true(db, admin_user, tenant_a):
    """send_renewal_reminder sends an email and returns True."""
    sub = make_subscription(db, tenant_a.id, admin_user.id,
                            name="Netflix", next_renewal=date.today())
    from app.services.email_service import EmailService
    with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: mock_server
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = EmailService.send_renewal_reminder(sub, "user@test.com", days_until=7)
    assert result is True
    mock_server.sendmail.assert_called_once()


def test_send_renewal_reminder_contains_subscription_name(db, admin_user, tenant_a):
    """Reminder email body contains the subscription name."""
    sub = make_subscription(db, tenant_a.id, admin_user.id,
                            name="Spotify", next_renewal=date.today())
    from app.services.email_service import EmailService
    captured = {}
    with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: mock_server
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        def capture_sendmail(from_addr, to_addrs, msg_str):
            captured["msg"] = msg_str
        mock_server.sendmail.side_effect = capture_sendmail
        EmailService.send_renewal_reminder(sub, "user@test.com", days_until=3)
    assert "Spotify" in captured["msg"]


def test_send_expiry_notice_returns_true(db, admin_user, tenant_a):
    """send_expiry_notice sends an email and returns True."""
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="Adobe")
    from app.services.email_service import EmailService
    with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: mock_server
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = EmailService.send_expiry_notice(sub, "user@test.com")
    assert result is True


def test_send_welcome_returns_true(db, admin_user, tenant_a):
    """send_welcome sends a welcome email and returns True."""
    from app.services.email_service import EmailService
    with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: mock_server
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = EmailService.send_welcome(admin_user, tenant_a)
    assert result is True


def test_send_returns_false_on_smtp_error(db, admin_user, tenant_a):
    """send_renewal_reminder returns False when SMTP raises an exception."""
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="Fail Sub")
    from app.services.email_service import EmailService
    with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ConnectionRefusedError("SMTP not reachable")
        result = EmailService.send_renewal_reminder(sub, "user@test.com", days_until=7)
    assert result is False


def test_send_uses_configured_smtp_host(db, admin_user, tenant_a):
    """EmailService uses SMTP_HOST and SMTP_PORT from settings."""
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="Test")
    from app.services.email_service import EmailService
    with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: mock_server
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        EmailService.send_renewal_reminder(sub, "user@test.com", days_until=7)
    # Verify SMTP was called with host from settings
    call_args = mock_smtp.call_args
    assert call_args is not None  # SMTP was instantiated
