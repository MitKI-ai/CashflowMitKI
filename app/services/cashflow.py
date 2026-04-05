"""CashflowService — aggregates all recurring streams into a monthly summary.

Cashflow = Σ StandingOrders(income)
         - Σ StandingOrders(expense)
         - Σ DirectDebits
         - Σ Subscriptions(active)
         - Σ StandingOrders(savings_transfer)
"""
from sqlalchemy.orm import Session

from app.models.direct_debit import DirectDebit
from app.models.standing_order import StandingOrder
from app.models.subscription import Subscription

FREQUENCY_MONTHLY_FACTOR = {
    "monthly": 1.0,
    "biweekly": 26 / 12,
    "quarterly": 1 / 3,
    "yearly": 1 / 12,
    "irregular": 1.0,
}

BILLING_CYCLE_MONTHLY_FACTOR = {
    "monthly": 1.0,
    "quarterly": 1 / 3,
    "yearly": 1 / 12,
    "biweekly": 26 / 12,
    "weekly": 52 / 12,
}


class CashflowService:
    @staticmethod
    def monthly_summary(db: Session, *, tenant_id: str) -> dict:
        # Standing orders
        standing_orders = (
            db.query(StandingOrder)
            .filter(StandingOrder.tenant_id == tenant_id, StandingOrder.is_active == True)
            .all()
        )

        monthly_income = 0.0
        monthly_expenses = 0.0
        monthly_savings = 0.0

        for so in standing_orders:
            factor = FREQUENCY_MONTHLY_FACTOR.get(so.frequency, 1.0)
            monthly = so.amount * factor
            if so.type == "income":
                monthly_income += monthly
            elif so.type == "expense":
                monthly_expenses += monthly
            elif so.type == "savings_transfer":
                monthly_savings += monthly

        # Direct debits
        direct_debits = (
            db.query(DirectDebit)
            .filter(DirectDebit.tenant_id == tenant_id, DirectDebit.is_active == True)
            .all()
        )

        monthly_direct_debits = 0.0
        for dd in direct_debits:
            factor = FREQUENCY_MONTHLY_FACTOR.get(dd.frequency, 1.0)
            monthly_direct_debits += dd.amount * factor

        # Subscriptions (active only)
        subscriptions = (
            db.query(Subscription)
            .filter(Subscription.tenant_id == tenant_id, Subscription.status == "active")
            .all()
        )

        monthly_subscriptions = 0.0
        for sub in subscriptions:
            factor = BILLING_CYCLE_MONTHLY_FACTOR.get(sub.billing_cycle, 1.0)
            monthly_subscriptions += sub.cost * factor

        monthly_net = (
            monthly_income
            - monthly_expenses
            - monthly_direct_debits
            - monthly_subscriptions
            - monthly_savings
        )

        return {
            "monthly_income": round(monthly_income, 2),
            "monthly_expenses": round(monthly_expenses, 2),
            "monthly_direct_debits": round(monthly_direct_debits, 2),
            "monthly_subscriptions": round(monthly_subscriptions, 2),
            "monthly_savings": round(monthly_savings, 2),
            "monthly_net": round(monthly_net, 2),
        }
