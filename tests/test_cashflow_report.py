"""Tests for Monthly Cashflow Report E-Mail — STORY-079."""
from unittest.mock import patch


def test_cashflow_report_email_template_renders():
    """The email template renders without errors."""
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader("app/templates/email"), autoescape=True)
    tpl = env.get_template("cashflow_report.html")
    html = tpl.render(
        user_name="Markus",
        month="M\u00e4rz 2026",
        income=4500.0,
        expenses=1200.0,
        direct_debits=310.0,
        subscriptions=45.0,
        savings=700.0,
        net=2245.0,
        net_worth=43200.0,
    )
    assert "Markus" in html
    assert "4500" in html
    assert "2245" in html


def test_cashflow_report_service_method():
    """EmailService.send_cashflow_report composes correct email."""
    from app.services.email_service import EmailService

    with patch.object(EmailService, "send", return_value=True) as mock_send:
        result = EmailService.send_cashflow_report(
            to="test@example.com",
            user_name="Markus",
            month="M\u00e4rz 2026",
            summary={
                "monthly_income": 4500.0,
                "monthly_expenses": 1200.0,
                "monthly_direct_debits": 310.0,
                "monthly_subscriptions": 45.0,
                "monthly_savings": 700.0,
                "monthly_net": 2245.0,
            },
            net_worth=43200.0,
        )
        assert result is True
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "test@example.com"
        assert "Cashflow" in call_args[0][1]
        assert "Markus" in call_args[0][2]


def test_internal_send_reports_endpoint(auth_client):
    """Internal API endpoint triggers report sending."""
    with patch("app.api.v1.internal.EmailService.send_cashflow_report", return_value=True) as mock:
        r = auth_client.post("/api/v1/internal/send-cashflow-reports",
                             headers={"X-Internal-Key": "test-internal-key"})
        assert r.status_code == 200
        data = r.json()
        assert "sent" in data
