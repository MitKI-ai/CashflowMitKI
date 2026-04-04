"""E-Mail Service — SMTP + Jinja2 templates (STORY-022)"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


def _render(template_name: str, ctx: dict) -> str:
    return _jinja_env.get_template(template_name).render(**ctx)


class EmailService:
    @staticmethod
    def send(to: str, subject: str, html: str) -> bool:
        """Send a plain HTML email via SMTP. Returns True on success."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.ehlo()
                if settings.smtp_user:
                    server.starttls()
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, [to], msg.as_string())
            return True
        except Exception as exc:
            logger.error("EmailService.send failed: %s", exc)
            return False

    @staticmethod
    def send_renewal_reminder(subscription, to: str, days_until: int) -> bool:
        ctx = {
            "subscription_name": subscription.name,
            "provider": subscription.provider or "",
            "cost": subscription.cost,
            "currency": subscription.currency,
            "billing_cycle": subscription.billing_cycle,
            "next_renewal": subscription.next_renewal,
            "days_until": days_until,
        }
        html = _render("renewal_reminder.html", ctx)
        subject = f"Erinnerung: {subscription.name} wird in {days_until} Tag(en) erneuert"
        return EmailService.send(to, subject, html)

    @staticmethod
    def send_expiry_notice(subscription, to: str) -> bool:
        ctx = {
            "subscription_name": subscription.name,
            "provider": subscription.provider or "",
            "cost": subscription.cost,
            "currency": subscription.currency,
            "end_date": subscription.end_date,
        }
        html = _render("expiry_notice.html", ctx)
        subject = f"Abonnement abgelaufen: {subscription.name}"
        return EmailService.send(to, subject, html)

    @staticmethod
    def send_invitation(to: str, invited_by: str, tenant_name: str, accept_url: str) -> bool:
        ctx = {
            "invited_by": invited_by,
            "tenant_name": tenant_name,
            "accept_url": accept_url,
        }
        html = _render("invitation.html", ctx)
        subject = f"Einladung zu {tenant_name} — mitKI.ai Subscription Manager"
        return EmailService.send(to, subject, html)

    @staticmethod
    def send_cashflow_report(
        to: str, user_name: str, month: str, summary: dict, net_worth: float = 0.0,
    ) -> bool:
        ctx = {
            "user_name": user_name,
            "month": month,
            "income": summary["monthly_income"],
            "expenses": summary["monthly_expenses"],
            "direct_debits": summary["monthly_direct_debits"],
            "subscriptions": summary["monthly_subscriptions"],
            "savings": summary["monthly_savings"],
            "net": summary["monthly_net"],
            "net_worth": net_worth,
        }
        html = _render("cashflow_report.html", ctx)
        subject = f"Dein Cashflow-Report: {month} — mitKI.ai"
        return EmailService.send(to, subject, html)

    @staticmethod
    def send_welcome(user, tenant) -> bool:
        ctx = {
            "display_name": user.display_name,
            "tenant_name": tenant.name,
        }
        html = _render("welcome.html", ctx)
        subject = "Willkommen beim mitKI.ai Subscription Manager"
        return EmailService.send(user.email, subject, html)
