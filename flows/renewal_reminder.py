"""Prefect Flow: Renewal Reminder — STORY-023

Runs daily. Calls the internal API to send reminder emails for subscriptions
renewing within the configured number of days.

Deploy to CT109:
  prefect deploy flows/renewal_reminder.py:renewal_reminder_flow \
    --name renewal-reminder-daily \
    --pool subscription-manager \
    --cron "0 8 * * *"
"""
import os

import httpx
from prefect import flow, get_run_logger, task


APP_BASE_URL = os.getenv("APP_BASE_URL", "http://192.168.1.17:8080")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
DAYS_AHEAD = int(os.getenv("REMINDER_DAYS_AHEAD", "7"))


@task(retries=2, retry_delay_seconds=60)
def call_renewal_reminders(days_ahead: int) -> dict:
    logger = get_run_logger()
    url = f"{APP_BASE_URL}/api/v1/internal/renewal-reminders"
    headers = {"X-Internal-Key": INTERNAL_API_KEY}
    resp = httpx.post(url, params={"days_ahead": days_ahead}, headers=headers, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    logger.info("Renewal reminders result: %s", result)
    return result


@flow(name="renewal-reminder", log_prints=True)
def renewal_reminder_flow(days_ahead: int = DAYS_AHEAD):
    """Send renewal reminder emails for subscriptions due within `days_ahead` days."""
    logger = get_run_logger()
    logger.info("Starting renewal reminder flow (days_ahead=%d)", days_ahead)
    result = call_renewal_reminders(days_ahead)
    logger.info("Done: sent=%d, total_due=%d", result.get("sent", 0), result.get("total_due", 0))
    return result


if __name__ == "__main__":
    renewal_reminder_flow()
