import calendar as cal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.account import Account
from app.models.cashflow_snapshot import CashflowSnapshot
from app.models.direct_debit import DirectDebit
from app.models.investment import Investment
from app.models.savings_goal import SavingsGoal
from app.models.standing_order import StandingOrder
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.cashflow_snapshot import SnapshotCreate, SnapshotResponse, TrendResponse
from app.services.cashflow import CashflowService

router = APIRouter(prefix="/cashflow", tags=["cashflow"])


@router.get("/summary")
def cashflow_summary(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return CashflowService.monthly_summary(db, tenant_id=tenant_id)


@router.get("/monthly-summary")
def monthly_summary(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    date_from = f"{year}-{mon:02d}-01"
    date_to = f"{year}-{mon+1:02d}-01" if mon < 12 else f"{year+1}-01-01"

    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.tenant_id == tenant_id,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date < date_to,
        )
        .all()
    )

    income = sum(t.amount for t in transactions if t.type == "income")
    expenses = sum(t.amount for t in transactions if t.type == "expense")

    return {
        "month": month,
        "income": income,
        "expenses": expenses,
        "net": income - expenses,
    }


@router.get("/net-worth")
def net_worth(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    accounts_total = (
        db.query(Account)
        .filter(Account.tenant_id == tenant_id, Account.is_active == True)
        .all()
    )
    accounts_sum = sum(a.balance for a in accounts_total)

    investments_total = (
        db.query(Investment)
        .filter(Investment.tenant_id == tenant_id, Investment.is_active == True)
        .all()
    )
    investments_sum = sum(i.current_value for i in investments_total)

    savings_goals = (
        db.query(SavingsGoal)
        .filter(SavingsGoal.tenant_id == tenant_id, SavingsGoal.is_active == True)
        .all()
    )
    savings_sum = sum(g.current_amount for g in savings_goals)

    return {
        "accounts_total": float(accounts_sum),
        "investments_total": float(investments_sum),
        "savings_goals_total": float(savings_sum),
        "net_worth": float(accounts_sum + investments_sum),
    }


# ── Snapshots ────────────────────────────────────────────────────────

def _compute_net_worth(db: Session, tenant_id: str) -> float:
    accounts_sum = sum(
        a.balance for a in db.query(Account).filter(
            Account.tenant_id == tenant_id, Account.is_active == True
        ).all()
    )
    investments_sum = sum(
        i.current_value for i in db.query(Investment).filter(
            Investment.tenant_id == tenant_id, Investment.is_active == True
        ).all()
    )
    return float(accounts_sum + investments_sum)


@router.get("/snapshots", response_model=list[SnapshotResponse])
def list_snapshots(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return (
        db.query(CashflowSnapshot)
        .filter(CashflowSnapshot.tenant_id == tenant_id)
        .order_by(CashflowSnapshot.month.asc())
        .all()
    )


@router.post("/snapshots", response_model=SnapshotResponse, status_code=201)
def create_snapshot(
    data: SnapshotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    summary = CashflowService.monthly_summary(db, tenant_id=tenant_id)
    nw = _compute_net_worth(db, tenant_id)

    snapshot = CashflowSnapshot(
        tenant_id=tenant_id,
        created_by_id=current_user.id,
        month=data.month,
        monthly_income=summary["monthly_income"],
        monthly_expenses=summary["monthly_expenses"],
        monthly_direct_debits=summary["monthly_direct_debits"],
        monthly_subscriptions=summary["monthly_subscriptions"],
        monthly_savings=summary["monthly_savings"],
        monthly_net=summary["monthly_net"],
        net_worth=nw,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@router.get("/trend", response_model=TrendResponse)
def cashflow_trend(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    snapshots = (
        db.query(CashflowSnapshot)
        .filter(CashflowSnapshot.tenant_id == tenant_id)
        .order_by(CashflowSnapshot.month.asc())
        .all()
    )
    return {
        "months": [s.month for s in snapshots],
        "income": [s.monthly_income for s in snapshots],
        "expenses": [s.monthly_expenses + s.monthly_direct_debits + s.monthly_subscriptions for s in snapshots],
        "net": [s.monthly_net for s in snapshots],
        "net_worth": [s.net_worth for s in snapshots],
    }


# ── Calendar ─────────────────────────────────────────────────────────

@router.get("/calendar")
def cashflow_calendar(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    num_days = cal.monthrange(year, mon)[1]

    standing_orders = (
        db.query(StandingOrder)
        .filter(StandingOrder.tenant_id == tenant_id, StandingOrder.is_active == True)
        .all()
    )
    direct_debits = (
        db.query(DirectDebit)
        .filter(DirectDebit.tenant_id == tenant_id, DirectDebit.is_active == True)
        .all()
    )

    days = []
    running_balance = 0.0
    for day_num in range(1, num_days + 1):
        entries = []
        for so in standing_orders:
            if so.execution_day == day_num:
                entry_type = "income" if so.type == "income" else ("savings" if so.type == "savings_transfer" else "expense")
                entries.append({"name": so.name, "amount": so.amount, "type": entry_type})
                if so.type == "income":
                    running_balance += so.amount
                else:
                    running_balance -= so.amount
        for dd in direct_debits:
            if dd.expected_day == day_num:
                entries.append({"name": dd.name, "amount": dd.amount, "type": "expense"})
                running_balance -= dd.amount
        days.append({
            "day": day_num,
            "entries": entries,
            "running_balance": round(running_balance, 2),
        })

    return {"month": month, "days": days}


# ── Simulator ────────────────────────────────────────────────────────

from pydantic import BaseModel  # noqa: E402


class SimulateRequest(BaseModel):
    income_adjustment: float = 0.0
    expense_adjustment: float = 0.0
    savings_adjustment: float = 0.0


@router.post("/simulate")
def cashflow_simulate(
    data: SimulateRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    current = CashflowService.monthly_summary(db, tenant_id=tenant_id)

    scenario = {
        "monthly_income": current["monthly_income"] + data.income_adjustment,
        "monthly_expenses": current["monthly_expenses"] + data.expense_adjustment,
        "monthly_direct_debits": current["monthly_direct_debits"],
        "monthly_subscriptions": current["monthly_subscriptions"],
        "monthly_savings": current["monthly_savings"] + data.savings_adjustment,
    }
    scenario["monthly_net"] = (
        scenario["monthly_income"]
        - scenario["monthly_expenses"]
        - scenario["monthly_direct_debits"]
        - scenario["monthly_subscriptions"]
        - scenario["monthly_savings"]
    )

    diff = {k: round(scenario[k] - current[k], 2) for k in current if k in scenario}

    return {"current": current, "scenario": scenario, "diff": diff}


# ── Purchasing Power ─────────────────────────────────────────────────

class PurchasingPowerRequest(BaseModel):
    nominal_value: float
    years: int
    inflation_rate: float = 2.0


@router.post("/purchasing-power")
def purchasing_power(data: PurchasingPowerRequest):
    rate = data.inflation_rate / 100
    real_value = data.nominal_value / ((1 + rate) ** data.years) if rate > 0 else data.nominal_value
    loss_pct = (1 - real_value / data.nominal_value) * 100 if data.nominal_value else 0.0

    yearly = []
    for y in range(1, data.years + 1):
        rv = data.nominal_value / ((1 + rate) ** y) if rate > 0 else data.nominal_value
        yearly.append({"year": y, "real_value": round(rv, 2)})

    return {
        "nominal_value": data.nominal_value,
        "real_value": round(real_value, 2),
        "purchasing_power_loss_pct": round(loss_pct, 2),
        "inflation_rate": data.inflation_rate,
        "years": data.years,
        "yearly_breakdown": yearly,
    }


# ── Tax Estimation ───────────────────────────────────────────────────

DEFAULT_TAX_RATE = 26.375  # Abgeltungssteuer 25% + 5.5% Soli
DEFAULT_ALLOWANCE = 1000.0  # Sparerpauschbetrag


class TaxEstimateRequest(BaseModel):
    capital_gains: float
    tax_free_allowance: float = DEFAULT_ALLOWANCE
    tax_rate: float = DEFAULT_TAX_RATE


@router.post("/tax-estimate")
def tax_estimate(data: TaxEstimateRequest):
    taxable = max(0.0, data.capital_gains - data.tax_free_allowance)
    tax = taxable * data.tax_rate / 100
    net = data.capital_gains - tax
    effective = (tax / data.capital_gains * 100) if data.capital_gains > 0 else 0.0
    return {
        "capital_gains": data.capital_gains,
        "tax_free_allowance": data.tax_free_allowance,
        "taxable_gains": round(taxable, 2),
        "tax_rate": data.tax_rate,
        "tax_amount": round(tax, 2),
        "net_gains": round(net, 2),
        "effective_tax_rate": round(effective, 2),
    }
