"""Tests — Auto-Buchungen (EPIC-212 / Sprint 19)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.direct_debit import DirectDebit
from app.models.standing_order import StandingOrder
from app.models.transaction import Transaction
from app.models.tenant import Tenant
from app.models.user import User
from app.services.booking_service import BookingService, _fires_this_month


# ── Unit: _fires_this_month ───────────────────────────────────────────────────

def test_fires_monthly():
    for m in range(1, 13):
        assert _fires_this_month("monthly", 2026, m)


def test_fires_quarterly():
    assert _fires_this_month("quarterly", 2026, 3)
    assert _fires_this_month("quarterly", 2026, 6)
    assert _fires_this_month("quarterly", 2026, 9)
    assert _fires_this_month("quarterly", 2026, 12)
    assert not _fires_this_month("quarterly", 2026, 1)
    assert not _fires_this_month("quarterly", 2026, 7)


def test_fires_yearly():
    assert _fires_this_month("yearly", 2026, 1)
    assert not _fires_this_month("yearly", 2026, 4)


def test_fires_biweekly():
    assert _fires_this_month("biweekly", 2026, 5)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def account(db: Session, tenant_a: Tenant, admin_user: User) -> Account:
    acc = Account(
        tenant_id=tenant_a.id,
        created_by_id=admin_user.id,
        name="Girokonto",
        type="checking",
        balance=5000.0,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


@pytest.fixture
def standing_order(db: Session, tenant_a: Tenant, admin_user: User, account: Account) -> StandingOrder:
    so = StandingOrder(
        tenant_id=tenant_a.id,
        created_by_id=admin_user.id,
        account_id=account.id,
        name="Gehalt",
        type="income",
        amount=4500.0,
        frequency="monthly",
        execution_day=27,
    )
    db.add(so)
    db.commit()
    db.refresh(so)
    return so


@pytest.fixture
def direct_debit(db: Session, tenant_a: Tenant, admin_user: User, account: Account) -> DirectDebit:
    dd = DirectDebit(
        tenant_id=tenant_a.id,
        created_by_id=admin_user.id,
        account_id=account.id,
        name="Strom EnBW",
        creditor="EnBW",
        amount=85.0,
        frequency="monthly",
        expected_day=5,
    )
    db.add(dd)
    db.commit()
    db.refresh(dd)
    return dd


# ── Unit: BookingService ──────────────────────────────────────────────────────

def test_generate_pending_standing_order(db, tenant_a, standing_order):
    pending = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=3
    )
    assert len(pending) == 1
    b = pending[0]
    assert b["description"] == "Gehalt"
    assert b["amount"] == 4500.0
    assert b["type"] == "income"
    assert b["is_recurring"] is True
    assert b["transaction_date"] == "2026-03-27"


def test_generate_pending_direct_debit(db, tenant_a, direct_debit):
    pending = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=3
    )
    assert len(pending) == 1
    b = pending[0]
    assert b["description"] == "Strom EnBW"
    assert b["type"] == "expense"


def test_generate_pending_both(db, tenant_a, standing_order, direct_debit):
    pending = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=3
    )
    assert len(pending) == 2


def test_no_duplicate_generation(db, tenant_a, admin_user, standing_order):
    """After confirming once, the same month must not re-generate the booking."""
    pending = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=3
    )
    BookingService.confirm_bookings(
        db, tenant_id=tenant_a.id, user_id=admin_user.id, bookings=pending
    )
    pending2 = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=3
    )
    assert pending2 == []


def test_quarterly_not_fired_in_january(db, tenant_a, admin_user, account):
    dd = DirectDebit(
        tenant_id=tenant_a.id,
        created_by_id=admin_user.id,
        account_id=account.id,
        name="GEZ",
        creditor="ARD",
        amount=55.08,
        frequency="quarterly",
        expected_day=15,
    )
    db.add(dd)
    db.commit()

    pending = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=1
    )
    assert len(pending) == 0

    pending_q = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=3
    )
    assert len(pending_q) == 1


def test_inactive_standing_order_skipped(db, tenant_a, standing_order):
    standing_order.is_active = False
    db.commit()
    pending = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=3
    )
    assert pending == []


def test_confirm_creates_transactions(db, tenant_a, admin_user, standing_order):
    pending = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=3
    )
    created = BookingService.confirm_bookings(
        db, tenant_id=tenant_a.id, user_id=admin_user.id, bookings=pending
    )
    assert len(created) == 1
    assert created[0].description == "Gehalt"
    assert db.query(Transaction).filter(Transaction.tenant_id == tenant_a.id).count() == 1


def test_tenant_isolation(db, tenant_a, tenant_b, admin_user, admin_b, account):
    """Bookings from tenant_b must not appear for tenant_a."""
    so_b = StandingOrder(
        tenant_id=tenant_b.id,
        created_by_id=admin_b.id,
        account_id=account.id,  # account belongs to tenant_a, but we just need a valid UUID
        name="Andere Firma Gehalt",
        type="income",
        amount=9999.0,
        frequency="monthly",
        execution_day=1,
    )
    db.add(so_b)
    db.commit()

    pending_a = BookingService.generate_pending(
        db, tenant_id=tenant_a.id, year=2026, month=3
    )
    assert all(b["amount"] != 9999.0 for b in pending_a)


# ── API Integration tests ─────────────────────────────────────────────────────

def test_api_pending_empty(auth_client: TestClient):
    r = auth_client.get("/api/v1/bookings/pending?year=2026&month=3")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 0
    assert data["bookings"] == []


def test_api_pending_with_standing_order(
    auth_client: TestClient, db: Session, tenant_a: Tenant, admin_user: User, account: Account, standing_order: StandingOrder
):
    r = auth_client.get("/api/v1/bookings/pending?year=2026&month=3")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["bookings"][0]["description"] == "Gehalt"


def test_api_confirm(
    auth_client: TestClient, db: Session, tenant_a: Tenant, admin_user: User, account: Account, standing_order: StandingOrder
):
    r = auth_client.get("/api/v1/bookings/pending?year=2026&month=3")
    bookings = r.json()["bookings"]

    r2 = auth_client.post("/api/v1/bookings/confirm", json={"bookings": bookings})
    assert r2.status_code == 200
    assert r2.json()["created"] == 1

    # Second call must see no pending anymore
    r3 = auth_client.get("/api/v1/bookings/pending?year=2026&month=3")
    assert r3.json()["count"] == 0


def test_api_confirm_empty_400(auth_client: TestClient):
    r = auth_client.post("/api/v1/bookings/confirm", json={"bookings": []})
    assert r.status_code == 400


def test_api_generate_for_month_auto_confirm(
    auth_client: TestClient, db: Session, tenant_a: Tenant, admin_user: User, account: Account, standing_order: StandingOrder
):
    r = auth_client.post("/api/v1/bookings/generate-for-month?year=2026&month=3&auto_confirm=true")
    assert r.status_code == 200
    data = r.json()
    assert data["generated"] == 1
    assert data["auto_confirmed"] is True


def test_api_invalid_month(auth_client: TestClient):
    r = auth_client.get("/api/v1/bookings/pending?year=2026&month=13")
    assert r.status_code == 400
