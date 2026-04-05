"""Deploy Prefect flows to the subscription-manager work pool (Prefect 3.x).

Run on CT109:
  cd /home/aiworker
  PREFECT_API_URL=http://192.168.1.16:4200/api \
    /opt/prefect-venv/bin/python flows/deploy.py
"""
from prefect.flows import load_flow_from_entrypoint
from prefect.runner.storage import LocalStorage

FLOWS_DIR = "/home/aiworker/flows"
POOL = "subscription-manager"


def deploy_flow(entrypoint: str, name: str, cron: str, parameters: dict | None = None):
    flow = load_flow_from_entrypoint(entrypoint)
    flow.from_source(
        source=LocalStorage(path=FLOWS_DIR),
        entrypoint=entrypoint.split("/")[-1],  # relative filename
    ).deploy(
        name=name,
        work_pool_name=POOL,
        cron=cron,
        parameters=parameters or {},
        ignore_warnings=True,
        print_next_steps=False,
    )
    print(f"Deployed: {name}")


if __name__ == "__main__":
    deploy_flow(
        entrypoint=f"{FLOWS_DIR}/renewal_reminder.py:renewal_reminder_flow",
        name="renewal-reminder-daily",
        cron="0 8 * * *",
        parameters={"days_ahead": 7},
    )
    deploy_flow(
        entrypoint=f"{FLOWS_DIR}/auto_renewal.py:auto_renewal_flow",
        name="auto-renewal-daily",
        cron="0 6 * * *",
    )
