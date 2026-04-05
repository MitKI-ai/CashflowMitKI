"""Analytics Service — MRR, ARR, Churn — STORY-036"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.subscription import Subscription

_CYCLE_MONTHLY_FACTOR = {
    "weekly": 4.33,
    "monthly": 1.0,
    "quarterly": 1 / 3,
    "yearly": 1 / 12,
}


def _to_monthly(cost: float, billing_cycle: str) -> float:
    return cost * _CYCLE_MONTHLY_FACTOR.get(billing_cycle, 1.0)


class AnalyticsService:

    @staticmethod
    def summary(db: Session, tenant_id: str) -> dict:
        subs = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).all()
        active = [s for s in subs if s.status == "active"]
        cancelled = [s for s in subs if s.status == "cancelled"]

        mrr = sum(_to_monthly(s.cost, s.billing_cycle) for s in active)
        arr = mrr * 12
        total = len(subs)
        churn_rate = round(len(cancelled) / total * 100, 1) if total else 0.0

        return {
            "mrr": round(mrr, 2),
            "arr": round(arr, 2),
            "active_count": len(active),
            "total_count": total,
            "cancelled_count": len(cancelled),
            "churn_rate": churn_rate,
        }

    @staticmethod
    def mrr_history(db: Session, tenant_id: str, months: int = 6) -> list[dict]:
        """Approximate MRR history: use current active subscriptions projected back."""
        today = date.today()
        result = []
        for i in range(months - 1, -1, -1):
            # Use first day of month i months ago
            d = today.replace(day=1) - timedelta(days=i * 30)
            month_label = d.strftime("%Y-%m")
            # Active subs created before or during this month
            subs = db.query(Subscription).filter(
                Subscription.tenant_id == tenant_id,
                Subscription.status == "active",
                Subscription.created_at <= d.replace(day=28),
            ).all()
            mrr = sum(_to_monthly(s.cost, s.billing_cycle) for s in subs)
            result.append({"month": month_label, "mrr": round(mrr, 2)})
        return result
