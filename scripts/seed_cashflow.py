"""
Seed Script für Cashflow-Daten — STORY-058
==========================================
Erstellt realistische Demo-Daten für Persona "Markus, 38, Familienvater".

Usage:
    python scripts/seed_cashflow.py          # nur wenn DB leer
    python scripts/seed_cashflow.py --force  # löscht + erstellt neu
"""
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/subscriptions.db")
os.environ.setdefault("APP_SECRET_KEY", "seed-script-secret-key-32-chars-xx!")

from datetime import date

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.account import Account
from app.models.direct_debit import DirectDebit
from app.models.standing_order import StandingOrder
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.transfer import Transfer
from app.models.user import User


def seed_cashflow(db: Session, *, force: bool = False):
    """Seed cashflow demo data for persona Markus."""

    # Check if data exists
    existing = db.query(Account).first()
    if existing and not force:
        print("Cashflow data already exists. Use --force to recreate.")
        return

    if force:
        # Clean cashflow tables only
        db.query(Transfer).delete()
        db.query(DirectDebit).delete()
        db.query(StandingOrder).delete()
        db.query(Account).delete()
        db.commit()

    # Find or create tenant + user
    tenant = db.query(Tenant).filter(Tenant.slug == "demo-gmbh").first()
    if not tenant:
        tenant = Tenant(name="Demo GmbH", slug="demo-gmbh")
        db.add(tenant)
        db.flush()

    user = db.query(User).filter(User.email == "markus@demo.com").first()
    if not user:
        user = User(
            tenant_id=tenant.id,
            email="markus@demo.com",
            password_hash=hash_password("demo1234"),
            display_name="Markus Weber",
            role="admin",
        )
        db.add(user)
        db.flush()

    # ── Konten ────────────────────────────────────────────────────
    girokonto = Account(
        tenant_id=tenant.id, created_by_id=user.id,
        name="Girokonto Sparkasse", type="checking", bank_name="Sparkasse",
        balance=3200.00, currency="EUR", is_primary=True,
    )
    sparkonto = Account(
        tenant_id=tenant.id, created_by_id=user.id,
        name="Tagesgeld ING", type="savings", bank_name="ING",
        balance=12000.00, currency="EUR", interest_rate=2.0,
    )
    depot = Account(
        tenant_id=tenant.id, created_by_id=user.id,
        name="ETF-Depot Trade Republic", type="investment", bank_name="Trade Republic",
        balance=28000.00, currency="EUR",
    )
    db.add_all([girokonto, sparkonto, depot])
    db.flush()

    # ── Daueraufträge ─────────────────────────────────────────────
    standing_orders = [
        StandingOrder(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="Gehalt", type="income", recipient="Arbeitgeber AG",
            amount=4500.00, frequency="monthly", execution_day=27,
        ),
        StandingOrder(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="Kindergeld", type="income", recipient="Familienkasse",
            amount=250.00, frequency="monthly", execution_day=5,
        ),
        StandingOrder(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="Miete", type="expense", recipient="Vermieter GmbH",
            amount=1200.00, frequency="monthly", execution_day=1,
        ),
        StandingOrder(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="KFZ-Versicherung", type="expense", recipient="HUK-Coburg",
            amount=85.00, frequency="monthly", execution_day=1,
        ),
        StandingOrder(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="Haftpflichtversicherung", type="expense", recipient="Allianz",
            amount=15.00, frequency="monthly", execution_day=1,
        ),
        StandingOrder(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="ETF-Sparplan", type="savings_transfer", recipient="Trade Republic",
            amount=500.00, frequency="monthly", execution_day=1,
        ),
    ]
    db.add_all(standing_orders)

    # ── Lastschriften ─────────────────────────────────────────────
    direct_debits = [
        DirectDebit(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="Strom EnBW", creditor="EnBW Energie", amount=85.00,
            frequency="monthly", expected_day=5,
        ),
        DirectDebit(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="Gas Stadtwerke", creditor="Stadtwerke", amount=65.00,
            frequency="monthly", expected_day=5,
        ),
        DirectDebit(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="Vodafone Internet", creditor="Vodafone GmbH", amount=45.00,
            frequency="monthly", expected_day=3,
        ),
        DirectDebit(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="GEZ Rundfunkbeitrag", creditor="ARD ZDF",
            amount=55.08, frequency="quarterly", expected_day=15,
        ),
        DirectDebit(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="Fitnessstudio McFit", creditor="McFit GmbH", amount=35.00,
            frequency="monthly", expected_day=1,
        ),
        DirectDebit(
            tenant_id=tenant.id, created_by_id=user.id, account_id=girokonto.id,
            name="Handy Telekom", creditor="Deutsche Telekom", amount=25.00,
            frequency="monthly", expected_day=10,
        ),
    ]
    db.add_all(direct_debits)

    # ── Transfers ─────────────────────────────────────────────────
    transfers = [
        Transfer(
            tenant_id=tenant.id, created_by_id=user.id,
            from_account_id=girokonto.id, to_account_id=sparkonto.id,
            amount=200.00, description="Notgroschen-Sparen",
            transfer_date=date(2026, 3, 1), is_recurring=True, frequency="monthly",
        ),
        Transfer(
            tenant_id=tenant.id, created_by_id=user.id,
            from_account_id=girokonto.id, to_account_id=sparkonto.id,
            amount=150.00, description="Urlaubs-Rücklage",
            transfer_date=date(2026, 3, 1), is_recurring=True, frequency="monthly",
        ),
    ]
    db.add_all(transfers)

    # ── Investments ──────────────────────────────────────────────
    from app.models.investment import Investment
    investments = [
        Investment(
            tenant_id=tenant.id, created_by_id=user.id,
            name="MSCI World ETF", type="etf", broker="Trade Republic",
            isin="IE00B4L5Y983", current_value=28500.00, invested_amount=22000.00,
        ),
        Investment(
            tenant_id=tenant.id, created_by_id=user.id,
            name="Bitcoin", type="crypto", broker="Kraken",
            current_value=3200.00, invested_amount=2000.00,
        ),
        Investment(
            tenant_id=tenant.id, created_by_id=user.id,
            name="Festgeld 12M", type="bond", broker="ING",
            current_value=10000.00, invested_amount=10000.00,
        ),
    ]
    db.add_all(investments)

    # ── Savings Goals ────────────────────────────────────────────
    from app.models.savings_goal import SavingsGoal
    savings_goals = [
        SavingsGoal(
            tenant_id=tenant.id, created_by_id=user.id,
            name="Notgroschen", type="emergency",
            target_amount=15000.00, current_amount=8500.00,
        ),
        SavingsGoal(
            tenant_id=tenant.id, created_by_id=user.id,
            name="Familienurlaub Mallorca", type="vacation_luxury",
            target_amount=4000.00, current_amount=1200.00,
        ),
        SavingsGoal(
            tenant_id=tenant.id, created_by_id=user.id,
            name="Rente mit 65", type="retirement",
            target_amount=500000.00, current_amount=41700.00,
        ),
    ]
    db.add_all(savings_goals)

    # ── Transactions (letzte 2 Monate) ──────────────────────────
    from app.models.transaction import Transaction
    transactions = [
        Transaction(tenant_id=tenant.id, created_by_id=user.id, description="REWE Wocheneinkauf", amount=87.50, type="expense", category="food", transaction_date=date(2026, 3, 5)),
        Transaction(tenant_id=tenant.id, created_by_id=user.id, description="ALDI Einkauf", amount=42.30, type="expense", category="food", transaction_date=date(2026, 3, 12)),
        Transaction(tenant_id=tenant.id, created_by_id=user.id, description="Shell Tanken", amount=65.00, type="expense", category="transport", transaction_date=date(2026, 3, 8)),
        Transaction(tenant_id=tenant.id, created_by_id=user.id, description="Restaurant Bella Italia", amount=78.00, type="expense", category="dining", transaction_date=date(2026, 3, 15)),
        Transaction(tenant_id=tenant.id, created_by_id=user.id, description="Amazon Bestellung", amount=34.99, type="expense", category="other", transaction_date=date(2026, 3, 20)),
        Transaction(tenant_id=tenant.id, created_by_id=user.id, description="Nebenjob Freelance", amount=450.00, type="income", category="income", transaction_date=date(2026, 3, 18)),
        Transaction(tenant_id=tenant.id, created_by_id=user.id, description="DM Drogerie", amount=23.50, type="expense", category="other", transaction_date=date(2026, 2, 25)),
        Transaction(tenant_id=tenant.id, created_by_id=user.id, description="Lidl Einkauf", amount=55.80, type="expense", category="food", transaction_date=date(2026, 2, 15)),
    ]
    db.add_all(transactions)

    # ── Retirement Profile ───────────────────────────────────────
    from app.models.retirement_profile import RetirementProfile
    retirement = RetirementProfile(
        tenant_id=tenant.id, user_id=user.id,
        current_age=38, retirement_age=65, life_expectancy=85,
        desired_monthly_income=2500.00, expected_pension=1200.00,
        current_savings=41700.00, expected_return_pct=5.0,
    )
    db.add(retirement)

    # ── Budget Alerts ────────────────────────────────────────────
    from app.models.budget_alert import BudgetAlert
    budget_alerts = [
        BudgetAlert(tenant_id=tenant.id, created_by_id=user.id, name="Lebensmittel", category="food", monthly_limit=400.00),
        BudgetAlert(tenant_id=tenant.id, created_by_id=user.id, name="Essen gehen", category="dining", monthly_limit=150.00),
        BudgetAlert(tenant_id=tenant.id, created_by_id=user.id, name="Transport", category="transport", monthly_limit=200.00),
    ]
    db.add_all(budget_alerts)

    db.commit()

    # Summary
    acc_count = db.query(Account).filter(Account.tenant_id == tenant.id).count()
    so_count = db.query(StandingOrder).filter(StandingOrder.tenant_id == tenant.id).count()
    dd_count = db.query(DirectDebit).filter(DirectDebit.tenant_id == tenant.id).count()
    tr_count = db.query(Transfer).filter(Transfer.tenant_id == tenant.id).count()
    inv_count = db.query(Investment).filter(Investment.tenant_id == tenant.id).count()
    sg_count = db.query(SavingsGoal).filter(SavingsGoal.tenant_id == tenant.id).count()
    tx_count = db.query(Transaction).filter(Transaction.tenant_id == tenant.id).count()

    print(f"Cashflow seed complete for tenant '{tenant.name}':")
    print(f"  {acc_count} Konten")
    print(f"  {so_count} Daueraufträge")
    print(f"  {dd_count} Lastschriften")
    print(f"  {tr_count} Transfers")
    print(f"  {inv_count} Geldanlagen")
    print(f"  {sg_count} Sparziele")
    print(f"  {tx_count} Transaktionen")
    print(f"  1 Renten-Profil")
    print(f"  3 Budget-Warnungen")
    print(f"  Login: markus@demo.com / demo1234")


if __name__ == "__main__":
    force = "--force" in sys.argv
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_cashflow(db, force=force)
