import os

# Must be set BEFORE any app imports so Settings() reads test values
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["APP_SECRET_KEY"] = "test-secret-key-32-chars-minimum-x!"
os.environ["IS_PRODUCTION"] = "false"
os.environ["INTERNAL_API_KEY"] = "test-internal-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine, get_db
from app.main import app
from app.models.category import Category
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.user import User


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate all tables before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(reset_db) -> Session:
    """Provides a DB session AND sets the FastAPI dependency override for all clients."""
    session = SessionLocal()

    def override():
        yield session

    app.dependency_overrides[get_db] = override
    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.pop(get_db, None)


def _new_client() -> TestClient:
    """Creates a fresh TestClient with its own cookie jar (= separate session)."""
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def client(db: Session) -> TestClient:
    """Unauthenticated client."""
    with _new_client() as c:
        yield c


@pytest.fixture
def tenant_a(db: Session) -> Tenant:
    t = Tenant(name="Acme GmbH", slug="acme-gmbh")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def tenant_b(db: Session) -> Tenant:
    t = Tenant(name="Other Corp", slug="other-corp")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def admin_user(db: Session, tenant_a: Tenant) -> User:
    u = User(
        tenant_id=tenant_a.id,
        email="admin@test.com",
        password_hash=hash_password("password123"),
        display_name="Test Admin",
        role="admin",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def regular_user(db: Session, tenant_a: Tenant) -> User:
    u = User(
        tenant_id=tenant_a.id,
        email="user@test.com",
        password_hash=hash_password("password123"),
        display_name="Test User",
        role="user",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def admin_b(db: Session, tenant_b: Tenant) -> User:
    u = User(
        tenant_id=tenant_b.id,
        email="admin-b@test.com",
        password_hash=hash_password("password123"),
        display_name="Admin B",
        role="admin",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def auth_client(db: Session, admin_user: User) -> TestClient:
    """Independent TestClient authenticated as tenant_a admin."""
    with _new_client() as c:
        r = c.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "password123"})
        assert r.status_code == 200, r.text
        yield c


@pytest.fixture
def user_client(db: Session, regular_user: User) -> TestClient:
    """Independent TestClient authenticated as tenant_a regular user."""
    with _new_client() as c:
        c.post("/api/v1/auth/login", json={"email": "user@test.com", "password": "password123"})
        yield c


@pytest.fixture
def auth_client_b(db: Session, admin_b: User) -> TestClient:
    """Independent TestClient authenticated as tenant_b admin (separate cookie jar)."""
    with _new_client() as c:
        c.post("/api/v1/auth/login", json={"email": "admin-b@test.com", "password": "password123"})
        yield c


# ── Test data helpers ─────────────────────────────────────────────────────────

def make_subscription(db: Session, tenant_id: str, user_id: str, **kwargs) -> Subscription:
    from datetime import date
    defaults = {
        "name": "Test Abo",
        "provider": "TestProvider",
        "cost": 9.99,
        "currency": "EUR",
        "billing_cycle": "monthly",
        "status": "active",
        "start_date": date.today(),
    }
    defaults.update(kwargs)
    sub = Subscription(tenant_id=tenant_id, created_by_id=user_id, **defaults)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def make_category(db: Session, tenant_id: str, name: str = "Test Kategorie", color: str = "#FF0000") -> Category:
    cat = Category(tenant_id=tenant_id, name=name, color=color)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat
