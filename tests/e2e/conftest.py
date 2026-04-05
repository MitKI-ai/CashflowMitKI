"""
Playwright E2E Test Konfiguration
==================================
Startet einen echten uvicorn-Server in einem Background-Thread.
Playwright öffnet einen echten Chromium-Browser und klickt durch die echte UI.

Unterschied zu Unit-Tests:
  Unit-Tests:      TestClient → simuliert HTTP, kein Browser
  Playwright-Tests: echtes Chromium → echter Server → echte HTML-Seiten

WICHTIG zu Datenbankisolation:
  Die E2E-Tests laufen in einer eigenen pytest-Session via:
    pytest tests/e2e/ -v
  Damit läuft nur tests/e2e/conftest.py (nicht tests/conftest.py).
  Wenn beide Conftest-Dateien gleichzeitig geladen werden, gewinnt
  die App's bestehende Engine (tests/conftest.py setzt DATABASE_URL zuerst).
  Daher: _seed_test_db() nutzt app.database.engine direkt.
"""
import os
import threading
import time

import pytest
import uvicorn

# ENV VOR App-Import setzen
os.environ.setdefault("DATABASE_URL", "sqlite:///./e2e_test.db")
os.environ.setdefault("APP_SECRET_KEY", "e2e-secret-key-32-chars-minimum-xx!")
os.environ.setdefault("IS_PRODUCTION", "false")
os.environ.setdefault("INTERNAL_API_KEY", "e2e-internal-key")

E2E_PORT = 8765
BASE_URL = f"http://127.0.0.1:{E2E_PORT}"


class ServerThread(threading.Thread):
    """Startet uvicorn in einem Background-Thread."""

    def __init__(self):
        super().__init__(daemon=True)
        self.server: uvicorn.Server | None = None

    def run(self):
        from app.main import app
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=E2E_PORT,
            log_level="warning",
        )
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


def _seed_test_db():
    """
    Legt Demo-Daten in die App-Datenbank — nutzt das engine der App,
    damit Server und Seed dieselbe Datei verwenden.
    """
    from datetime import date

    from sqlalchemy.orm import Session

    from app.core.security import hash_password
    from app.database import Base, engine  # ← App's eigenes engine
    from app.models.plan import Plan
    from app.models.subscription import Subscription
    from app.models.tenant import Tenant
    from app.models.user import User

    # Sauber neu starten
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        tenant = Tenant(name="Demo GmbH", slug="demo-gmbh")
        db.add(tenant)
        db.flush()

        admin = User(
            tenant_id=tenant.id,
            email="admin@demo.com",
            password_hash=hash_password("demo1234"),
            display_name="Demo Admin",
            role="admin",
        )
        db.add(admin)
        db.flush()

        Plan(
            tenant_id=tenant.id,
            name="Basic",
            price=9.99,
            currency="EUR",
            billing_cycle="monthly",
            features_json='["Feature A", "Feature B"]',
        )

        sub = Subscription(
            tenant_id=tenant.id,
            created_by_id=admin.id,
            name="Netflix",
            provider="Netflix Inc.",
            cost=17.99,
            currency="EUR",
            billing_cycle="monthly",
            status="active",
            start_date=date.today(),
        )
        db.add(sub)
        db.commit()


@pytest.fixture(autouse=True)
def reset_db():
    """
    Überschreibt tests/conftest.py reset_db.
    E2E-Tests brauchen kein DB-Reset pro Test — der Server läuft mit
    persistenten Demo-Daten für die gesamte Session.
    """
    yield  # nichts tun


@pytest.fixture(scope="session")
def live_server():
    """
    Session-scoped: Server läuft einmal für alle E2E-Tests.
    """
    _seed_test_db()

    server_thread = ServerThread()
    server_thread.start()

    # Warten bis Server bereit ist (max 9 Sekunden)
    import httpx
    for _ in range(30):
        try:
            httpx.get(f"{BASE_URL}/health", timeout=1)
            break
        except Exception:
            time.sleep(0.3)
    else:
        raise RuntimeError(f"Server auf Port {E2E_PORT} nicht erreichbar")

    yield BASE_URL

    server_thread.stop()


@pytest.fixture(scope="session")
def base_url(live_server):
    """URL des Test-Servers — von pytest-playwright automatisch erkannt."""
    return live_server
