import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.account import Account
from app.models.direct_debit import DirectDebit
from app.models.investment import Investment
from app.models.savings_goal import SavingsGoal
from app.models.standing_order import StandingOrder
from app.models.user import User
from app.models.widget_config import WidgetConfig
from app.services.cashflow import CashflowService

router = APIRouter(prefix="/widgets", tags=["widgets"])

# ── Widget Registry ──────────────────────────────────────────────────

WIDGET_REGISTRY = [
    {"id": "net_cashflow", "title": "Netto-Cashflow", "type": "kpi", "size": "1x1"},
    {"id": "net_worth", "title": "Gesamtvermögen", "type": "kpi", "size": "1x1"},
    {"id": "savings_rate", "title": "Sparquote", "type": "kpi", "size": "1x1"},
    {"id": "next_payments", "title": "Nächste 5 Zahlungen", "type": "list", "size": "2x1"},
    {"id": "budget_status", "title": "Budget-Status", "type": "list", "size": "2x1"},
    {"id": "savings_progress", "title": "Sparziel-Fortschritt", "type": "chart", "size": "2x1"},
    {"id": "monthly_trend", "title": "Monats-Trend", "type": "chart", "size": "2x2"},
    {"id": "asset_allocation", "title": "Vermögens-Aufteilung", "type": "chart", "size": "2x1"},
]

DEFAULT_WIDGETS = ["net_cashflow", "net_worth", "savings_rate", "next_payments",
                   "savings_progress", "monthly_trend"]

PRESETS = {
    "sparer": {
        "name": "sparer",
        "title": "Sparer",
        "widgets": ["net_cashflow", "savings_rate", "savings_progress", "budget_status", "monthly_trend"],
    },
    "familie": {
        "name": "familie",
        "title": "Familie",
        "widgets": ["net_cashflow", "net_worth", "next_payments", "budget_status", "savings_progress", "monthly_trend"],
    },
    "investor": {
        "name": "investor",
        "title": "Investor",
        "widgets": ["net_worth", "asset_allocation", "savings_rate", "monthly_trend", "net_cashflow"],
    },
}


@router.get("/available")
def list_available_widgets():
    return WIDGET_REGISTRY


@router.get("/presets")
def list_presets():
    return list(PRESETS.values())


# ── User Config ──────────────────────────────────────────────────────

def _get_or_create_config(db: Session, user: User, tenant_id: str) -> WidgetConfig:
    config = db.query(WidgetConfig).filter(WidgetConfig.user_id == user.id).first()
    if not config:
        config = WidgetConfig(
            tenant_id=tenant_id, user_id=user.id,
            widgets_json=json.dumps(DEFAULT_WIDGETS),
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


class WidgetConfigResponse(BaseModel):
    widgets: list[str]


class WidgetConfigUpdate(BaseModel):
    widgets: list[str]


class PresetApply(BaseModel):
    preset: str


@router.get("/config", response_model=WidgetConfigResponse)
def get_widget_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    config = _get_or_create_config(db, current_user, tenant_id)
    return {"widgets": json.loads(config.widgets_json)}


@router.put("/config", response_model=WidgetConfigResponse)
def update_widget_config(
    data: WidgetConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    config = _get_or_create_config(db, current_user, tenant_id)
    config.widgets_json = json.dumps(data.widgets)
    db.commit()
    return {"widgets": data.widgets}


@router.post("/apply-preset", response_model=WidgetConfigResponse)
def apply_preset(
    data: PresetApply,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    preset = PRESETS.get(data.preset)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    config = _get_or_create_config(db, current_user, tenant_id)
    config.widgets_json = json.dumps(preset["widgets"])
    db.commit()
    return {"widgets": preset["widgets"]}


# ── Widget Data ──────────────────────────────────────────────────────

@router.get("/data/{widget_id}")
def get_widget_data(
    widget_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    valid_ids = {w["id"] for w in WIDGET_REGISTRY}
    if widget_id not in valid_ids:
        raise HTTPException(status_code=404, detail="Widget not found")

    if widget_id == "net_cashflow":
        summary = CashflowService.monthly_summary(db, tenant_id=tenant_id)
        return {"value": summary["monthly_net"], "label": "Netto-Cashflow", "unit": "EUR"}

    if widget_id == "net_worth":
        acc = sum(a.balance for a in db.query(Account).filter(
            Account.tenant_id == tenant_id, Account.is_active == True).all())
        inv = sum(i.current_value for i in db.query(Investment).filter(
            Investment.tenant_id == tenant_id, Investment.is_active == True).all())
        return {"value": float(acc + inv), "label": "Gesamtvermögen", "unit": "EUR"}

    if widget_id == "savings_rate":
        summary = CashflowService.monthly_summary(db, tenant_id=tenant_id)
        income = summary["monthly_income"]
        savings = summary["monthly_savings"]
        rate = (savings / income * 100) if income > 0 else 0.0
        return {"value": round(rate, 1), "label": "Sparquote", "unit": "%"}

    if widget_id == "next_payments":
        from datetime import date
        today = date.today()
        day = today.day
        sos = db.query(StandingOrder).filter(
            StandingOrder.tenant_id == tenant_id, StandingOrder.is_active == True,
            StandingOrder.type != "income", StandingOrder.execution_day > day,
        ).order_by(StandingOrder.execution_day).limit(5).all()
        return {"data": [{"name": so.name, "amount": so.amount, "day": so.execution_day} for so in sos]}

    if widget_id == "budget_status":
        from app.models.budget_alert import BudgetAlert
        alerts = db.query(BudgetAlert).filter(
            BudgetAlert.tenant_id == tenant_id, BudgetAlert.is_active == True
        ).all()
        return {"data": [{"name": a.name, "limit": a.monthly_limit, "category": a.category} for a in alerts]}

    if widget_id == "savings_progress":
        goals = db.query(SavingsGoal).filter(
            SavingsGoal.tenant_id == tenant_id, SavingsGoal.is_active == True
        ).all()
        return {"data": [{"name": g.name, "target": g.target_amount, "current": g.current_amount,
                          "pct": min(100, round(g.current_amount / g.target_amount * 100, 1)) if g.target_amount else 0}
                         for g in goals]}

    if widget_id == "monthly_trend":
        from app.models.cashflow_snapshot import CashflowSnapshot
        snaps = db.query(CashflowSnapshot).filter(
            CashflowSnapshot.tenant_id == tenant_id
        ).order_by(CashflowSnapshot.month.desc()).limit(6).all()
        snaps.reverse()
        return {"data": [{"month": s.month, "income": s.monthly_income, "net": s.monthly_net} for s in snaps]}

    if widget_id == "asset_allocation":
        acc = sum(a.balance for a in db.query(Account).filter(
            Account.tenant_id == tenant_id, Account.is_active == True).all())
        inv = sum(i.current_value for i in db.query(Investment).filter(
            Investment.tenant_id == tenant_id, Investment.is_active == True).all())
        return {"data": [{"label": "Konten", "value": float(acc)}, {"label": "Geldanlagen", "value": float(inv)}]}

    return {"value": 0}
