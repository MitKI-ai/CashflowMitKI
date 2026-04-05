"""BookingService — Auto-Buchungen aus Daueraufträgen & Lastschriften (EPIC-212).

Generates pending Transaction entries for a given year/month based on active
StandingOrders and DirectDebits.  Provides duplicate detection against already
existing Transactions so the same booking is never suggested twice.
"""
from calendar import monthrange
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models.direct_debit import DirectDebit
from app.models.standing_order import StandingOrder
from app.models.transaction import Transaction

# Which months a frequency fires
_QUARTERLY_MONTHS = {3, 6, 9, 12}


def _fires_this_month(frequency: str, year: int, month: int) -> bool:
    if frequency == "monthly":
        return True
    if frequency == "biweekly":
        return True
    if frequency == "quarterly":
        return month in _QUARTERLY_MONTHS
    if frequency == "yearly":
        return month == 1
    return True  # irregular — always suggest


def _clamp_day(day: int, year: int, month: int) -> int:
    """Clamp execution day to last valid day of month (e.g. day 31 in Feb → 28)."""
    last = monthrange(year, month)[1]
    return min(day, last)


def _dup_key(description: str, amount: float, year: int, month: int) -> str:
    return f"{description.lower().strip()}|{amount:.2f}|{year}-{month:02d}"


class BookingService:
    # ── generate ──────────────────────────────────────────────────────────────

    @staticmethod
    def generate_pending(
        db: Session,
        *,
        tenant_id: str,
        year: int,
        month: int,
    ) -> list[dict[str, Any]]:
        """Return a list of pending booking dicts (not yet committed to DB).

        Each dict has the shape accepted by `confirm_bookings()`.
        Already-existing Transactions for the same period are excluded.
        """
        # Build set of existing dup-keys for this month
        existing_txns = (
            db.query(Transaction)
            .filter(
                Transaction.tenant_id == tenant_id,
                Transaction.transaction_date >= date(year, month, 1),
                Transaction.transaction_date <= date(year, month, monthrange(year, month)[1]),
            )
            .all()
        )
        existing_keys = {
            _dup_key(t.description, t.amount, t.transaction_date.year, t.transaction_date.month)
            for t in existing_txns
        }

        pending: list[dict[str, Any]] = []

        # ── Standing Orders ────────────────────────────────────────────────────
        standing_orders = (
            db.query(StandingOrder)
            .filter(
                StandingOrder.tenant_id == tenant_id,
                StandingOrder.is_active == True,
            )
            .all()
        )

        for so in standing_orders:
            if not _fires_this_month(so.frequency, year, month):
                continue
            if so.end_date and so.end_date < date(year, month, 1):
                continue

            tx_type = "income" if so.type == "income" else "expense"
            category = "income" if so.type == "income" else "other"
            day = _clamp_day(so.execution_day, year, month)
            desc = so.name

            key = _dup_key(desc, so.amount, year, month)
            if key in existing_keys:
                continue

            pending.append({
                "source": "standing_order",
                "source_id": so.id,
                "account_id": so.account_id,
                "description": desc,
                "amount": so.amount,
                "type": tx_type,
                "category": category,
                "currency": so.currency,
                "transaction_date": date(year, month, day).isoformat(),
                "is_recurring": True,
                "duplicate": False,
            })

        # ── Direct Debits ──────────────────────────────────────────────────────
        direct_debits = (
            db.query(DirectDebit)
            .filter(
                DirectDebit.tenant_id == tenant_id,
                DirectDebit.is_active == True,
            )
            .all()
        )

        for dd in direct_debits:
            if not _fires_this_month(dd.frequency, year, month):
                continue

            day = _clamp_day(dd.expected_day, year, month)
            desc = dd.name
            key = _dup_key(desc, dd.amount, year, month)
            if key in existing_keys:
                continue

            pending.append({
                "source": "direct_debit",
                "source_id": dd.id,
                "account_id": dd.account_id,
                "description": desc,
                "amount": dd.amount,
                "type": "expense",
                "category": "other",
                "currency": dd.currency,
                "transaction_date": date(year, month, day).isoformat(),
                "is_recurring": True,
                "duplicate": False,
            })

        # Sort by date
        pending.sort(key=lambda b: b["transaction_date"])
        return pending

    # ── confirm ───────────────────────────────────────────────────────────────

    @staticmethod
    def confirm_bookings(
        db: Session,
        *,
        tenant_id: str,
        user_id: str,
        bookings: list[dict[str, Any]],
    ) -> list[Transaction]:
        """Persist a subset of pending bookings as Transactions."""
        created: list[Transaction] = []
        for b in bookings:
            tx = Transaction(
                tenant_id=tenant_id,
                created_by_id=user_id,
                account_id=b.get("account_id"),
                description=b["description"],
                amount=b["amount"],
                type=b["type"],
                category=b.get("category", "other"),
                currency=b.get("currency", "EUR"),
                transaction_date=date.fromisoformat(b["transaction_date"]),
                is_recurring=b.get("is_recurring", True),
            )
            db.add(tx)
            created.append(tx)
        db.commit()
        for tx in created:
            db.refresh(tx)
        return created
