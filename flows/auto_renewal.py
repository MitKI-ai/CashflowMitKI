"""Prefect Flow: Auto-Renewal + Expiry — STORY-024

Runs daily. Calls the internal API to:
- Advance next_renewal date for auto-renew subscriptions
- Set status=expired for overdue subscriptions and send expiry emails

Deploy to CT109:
  prefect deploy flows/auto_renewal.py:auto_renewal_flow \
    --name auto-renewal-daily \
    --pool subscription-manager \
    --cron "0 6 * * *"
"""
import os

import httpx
from prefect import flow, get_run_logger, task


APP_BASE_URL = os.getenv("APP_BASE_URL", "http://192.168.1.17:8080")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


@task(retries=2, retry_delay_seconds=60)
def call_process_renewals() -> dict:
    logger = get_run_logger()
    url = f"{APP_BASE_URL}/api/v1/internal/process-renewals"
    headers = {"X-Internal-Key": INTERNAL_API_KEY}
    resp = httpx.post(url, headers=headers, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    logger.info("Process renewals result: %s", result)
    return result


@flow(name="auto-renewal", log_prints=True)
def auto_renewal_flow():
    """Advance renewal dates and expire overdue subscriptions."""
    logger = get_run_logger()
    logger.info("Starting auto-renewal flow")
    result = call_process_renewals()
    logger.info("Done: renewed=%d, expired=%d", result.get("renewed", 0), result.get("expired", 0))
    return result


if __name__ == "__main__":
    auto_renewal_flow()
