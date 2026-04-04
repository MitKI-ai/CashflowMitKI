"""Prefect Flow: Monthly Cashflow Report + Auto-Buchungen — EPIC-208/212

Runs on the 1st of each month at 07:00.
1. Generates and confirms Auto-Buchungen for the previous month (if any still pending).
2. Sends the PDF cashflow report via e-mail to all active admin users.

Deploy to CT109:
  prefect deploy flows/monthly_report.py:monthly_report_flow \
    --name monthly-report \
    --pool subscription-manager \
    --cron "0 7 1 * *"
"""
import os
from datetime import date

import httpx
from prefect import flow, get_run_logger, task

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://192.168.1.17:8080")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
_HEADERS = {"X-Internal-Key": INTERNAL_API_KEY}


@task(retries=2, retry_delay_seconds=60)
def auto_confirm_bookings(year: int, month: int) -> dict:
    logger = get_run_logger()
    url = f"{APP_BASE_URL}/api/v1/internal/bookings/generate"
    resp = httpx.post(
        url,
        params={"year": year, "month": month, "auto_confirm": True},
        headers=_HEADERS,
        timeout=60,
    )
    resp.raise_for_status()
    result = resp.json()
    logger.info("Auto-Buchungen for %d/%02d: %s", year, month, result)
    return result


@task(retries=2, retry_delay_seconds=60)
def send_reports(year: int, month: int) -> dict:
    logger = get_run_logger()
    url = f"{APP_BASE_URL}/api/v1/internal/reports/send-all"
    resp = httpx.post(
        url,
        params={"year": year, "month": month},
        headers=_HEADERS,
        timeout=120,
    )
    resp.raise_for_status()
    result = resp.json()
    logger.info("Report emails for %d/%02d: %s", year, month, result)
    return result


@flow(name="monthly-report", log_prints=True)
def monthly_report_flow(year: int | None = None, month: int | None = None):
    """Generate bookings and send cashflow reports for the given month.

    Defaults to the *previous* month (run on the 1st of current month).
    """
    logger = get_run_logger()
    today = date.today()
    # Default: previous month
    if month is None:
        prev = today.replace(day=1)
        import calendar
        prev_month = prev.month - 1 or 12
        prev_year = prev.year if prev.month > 1 else prev.year - 1
        y, m = prev_year, prev_month
    else:
        y, m = year or today.year, month

    logger.info("Monthly report flow for %d/%02d", y, m)
    booking_result = auto_confirm_bookings(y, m)
    report_result = send_reports(y, m)
    return {"bookings": booking_result, "reports": report_result}
