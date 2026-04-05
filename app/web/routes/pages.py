import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.models.account import Account
from app.models.budget_alert import BudgetAlert
from app.models.category import Category
from app.models.direct_debit import DirectDebit
from app.models.investment import Investment
from app.models.retirement_profile import RetirementProfile
from app.models.savings_goal import SavingsGoal
from app.models.standing_order import StandingOrder
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.transaction import Transaction
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.cashflow import CashflowService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("pages/login.html", {"request": request, "user": None, "version": settings.app_version})


@router.post("/login")
def login_submit(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "pages/login.html",
            {"request": request, "error": "Ungültige Anmeldedaten", "user": None, "version": settings.app_version},
            status_code=401,
        )
    request.session["user_id"] = user.id
    request.session["tenant_id"] = user.tenant_id
    return RedirectResponse("/dashboard", status_code=302)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("pages/register.html", {"request": request, "user": None, "version": settings.app_version})


@router.post("/register")
def register_submit(
    request: Request,
    tenant_name: str = Form(...),
    display_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    slug = _slugify(tenant_name)
    if db.query(Tenant).filter(Tenant.slug == slug).first():
        return templates.TemplateResponse(
            "pages/register.html",
            {"request": request, "error": "Organisationsname bereits vergeben", "user": None, "version": settings.app_version},
        )
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse(
            "pages/register.html",
            {"request": request, "error": "E-Mail bereits registriert", "user": None, "version": settings.app_version},
        )

    tenant = Tenant(name=tenant_name, slug=slug)
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
        role="admin",
    )
    db.add(user)
    db.commit()

    request.session["user_id"] = user.id
    request.session["tenant_id"] = tenant.id
    return RedirectResponse("/dashboard", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    tenant_id = user.tenant_id
    subs = db.query(Subscription).filter(Subscription.tenant_id == tenant_id)
    active = subs.filter(Subscription.status == "active").all()
    all_subs = subs.all()

    today = date.today()
    renewals_7d = sum(1 for s in active if s.next_renewal and s.next_renewal <= today + timedelta(days=7))
    renewals_30d = [s for s in active if s.next_renewal and s.next_renewal <= today + timedelta(days=30)]
    monthly_cost = sum(s.cost for s in active if s.billing_cycle == "monthly")
    yearly_cost_monthly = sum(s.cost / 12 for s in active if s.billing_cycle == "yearly")
    quarterly_cost_monthly = sum(s.cost / 3 for s in active if s.billing_cycle == "quarterly")
    total_monthly = monthly_cost + yearly_cost_monthly + quarterly_cost_monthly

    recent = sorted(all_subs, key=lambda s: s.created_at, reverse=True)[:10]

    # Chart data: cost by billing cycle
    billing_cycles = ["monthly", "quarterly", "yearly"]
    cost_by_cycle = [
        round(sum(s.cost for s in active if s.billing_cycle == cycle), 2)
        for cycle in billing_cycles
    ]

    # Chart data: status distribution
    statuses = ["active", "paused", "cancelled", "trial"]
    status_counts = [sum(1 for s in all_subs if s.status == st) for st in statuses]

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "user": user,
            "version": settings.app_version,
            "stats": {
                "active_count": len(active),
                "total_count": len(all_subs),
                "monthly_cost": total_monthly,
                "renewals_7d": renewals_7d,
                "currency": tenant.currency if tenant else "EUR",
            },
            "recent_subs": recent,
            "renewals_30d": sorted(renewals_30d, key=lambda s: s.next_renewal),
            "chart_billing_labels": billing_cycles,
            "chart_billing_data": cost_by_cycle,
            "chart_status_labels": statuses,
            "chart_status_data": status_counts,
        },
    )


@router.get("/subscriptions", response_class=HTMLResponse)
def subscriptions_page(request: Request, status: str | None = None, category_id: str | None = None, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    query = db.query(Subscription).filter(Subscription.tenant_id == user.tenant_id)
    if status:
        query = query.filter(Subscription.status == status)
    if category_id:
        query = query.filter(Subscription.categories.any(Category.id == category_id))
    subs = query.order_by(Subscription.name).all()

    cats = db.query(Category).filter(Category.tenant_id == user.tenant_id).order_by(Category.name).all()

    return templates.TemplateResponse(
        "pages/subscriptions.html",
        {
            "request": request,
            "user": user,
            "version": settings.app_version,
            "subscriptions": subs,
            "filter_status": status,
            "filter_category_id": category_id,
            "categories": cats,
        },
    )


@router.get("/subscriptions/new", response_class=HTMLResponse)
def new_subscription(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        "pages/subscription_form.html",
        {"request": request, "user": user, "version": settings.app_version, "subscription": None},
    )


@router.post("/subscriptions/new")
def create_subscription(
    request: Request,
    name: str = Form(...),
    provider: str = Form(""),
    cost: float = Form(0.0),
    currency: str = Form("EUR"),
    billing_cycle: str = Form("monthly"),
    status: str = Form("active"),
    start_date: str = Form(""),
    next_renewal: str = Form(""),
    auto_renew: str = Form("false"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    sub = Subscription(
        tenant_id=user.tenant_id,
        created_by_id=user.id,
        name=name,
        provider=provider,
        cost=cost,
        currency=currency,
        billing_cycle=billing_cycle,
        status=status,
        start_date=date.fromisoformat(start_date) if start_date else date.today(),
        next_renewal=date.fromisoformat(next_renewal) if next_renewal else None,
        auto_renew=auto_renew == "true",
        notes=notes or None,
    )
    db.add(sub)
    db.commit()
    return RedirectResponse("/subscriptions", status_code=302)


@router.get("/subscriptions/{sub_id}/edit", response_class=HTMLResponse)
def edit_subscription(sub_id: str, request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    sub = db.query(Subscription).filter(Subscription.id == sub_id, Subscription.tenant_id == user.tenant_id).first()
    if not sub:
        return RedirectResponse("/subscriptions", status_code=302)
    return templates.TemplateResponse(
        "pages/subscription_form.html",
        {"request": request, "user": user, "version": settings.app_version, "subscription": sub},
    )


@router.post("/subscriptions/{sub_id}/edit")
def update_subscription(
    sub_id: str,
    request: Request,
    name: str = Form(...),
    provider: str = Form(""),
    cost: float = Form(0.0),
    currency: str = Form("EUR"),
    billing_cycle: str = Form("monthly"),
    status: str = Form("active"),
    start_date: str = Form(""),
    next_renewal: str = Form(""),
    auto_renew: str = Form("false"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    sub = db.query(Subscription).filter(Subscription.id == sub_id, Subscription.tenant_id == user.tenant_id).first()
    if not sub:
        return RedirectResponse("/subscriptions", status_code=302)

    sub.name = name
    sub.provider = provider
    sub.cost = cost
    sub.currency = currency
    sub.billing_cycle = billing_cycle
    sub.status = status
    sub.start_date = date.fromisoformat(start_date) if start_date else sub.start_date
    sub.next_renewal = date.fromisoformat(next_renewal) if next_renewal else None
    sub.auto_renew = auto_renew == "true"
    sub.notes = notes or None
    db.commit()
    return RedirectResponse("/subscriptions", status_code=302)


@router.post("/subscriptions/{sub_id}/delete")
def delete_subscription(sub_id: str, request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    sub = db.query(Subscription).filter(Subscription.id == sub_id, Subscription.tenant_id == user.tenant_id).first()
    if sub:
        db.delete(sub)
        db.commit()
    return RedirectResponse("/subscriptions", status_code=302)


# ── Categories ────────────────────────────────────────────────────────────────

@router.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if user.role != "admin":
        return RedirectResponse("/dashboard", status_code=302)
    cats = db.query(Category).filter(Category.tenant_id == user.tenant_id).order_by(Category.name).all()
    return templates.TemplateResponse(
        "pages/categories.html",
        {"request": request, "user": user, "version": settings.app_version, "categories": cats},
    )


@router.post("/categories/new")
def create_category(
    request: Request,
    name: str = Form(...),
    color: str = Form("#F97316"),
    icon: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/login", status_code=302)
    cat = Category(tenant_id=user.tenant_id, name=name, color=color, icon=icon or None)
    db.add(cat)
    db.commit()
    return RedirectResponse("/categories", status_code=302)


@router.post("/categories/{cat_id}/delete")
def delete_category_web(cat_id: str, request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/login", status_code=302)
    cat = db.query(Category).filter(Category.id == cat_id, Category.tenant_id == user.tenant_id).first()
    if cat:
        db.delete(cat)
        db.commit()
    return RedirectResponse("/categories", status_code=302)


# ── Tenant Settings ───────────────────────────────────────────────────────────

@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if user.role != "admin":
        return RedirectResponse("/dashboard", status_code=302)
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    return templates.TemplateResponse(
        "pages/settings.html",
        {"request": request, "user": user, "version": settings.app_version, "tenant": tenant},
    )


_VALID_LOCALES = {"de", "en"}


@router.post("/settings")
def update_settings(
    request: Request,
    name: str = Form(...),
    currency: str = Form("EUR"),
    locale: str = Form("de"),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/login", status_code=302)
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    tenant.name = name
    tenant.currency = currency
    if locale in _VALID_LOCALES:
        tenant.locale = locale
    db.commit()
    return templates.TemplateResponse(
        "pages/settings.html",
        {
            "request": request,
            "user": user,
            "version": settings.app_version,
            "tenant": tenant,
            "success": "Einstellungen gespeichert",
        },
    )


# ── User Management ──────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
def users_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if user.role != "admin":
        return RedirectResponse("/dashboard", status_code=302)
    users = db.query(User).filter(User.tenant_id == user.tenant_id).order_by(User.created_at).all()
    return templates.TemplateResponse(
        "pages/users.html",
        {"request": request, "user": user, "version": settings.app_version, "users": users},
    )


# ── Profile / Self-Service ────────────────────────────────────────────────────

@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        "pages/profile.html",
        {"request": request, "user": user, "version": settings.app_version},
    )


@router.post("/profile")
def update_profile(
    request: Request,
    display_name: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    user.display_name = display_name
    user.email = email
    db.commit()
    return RedirectResponse("/profile", status_code=302)


@router.post("/profile/password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if not verify_password(current_password, user.password_hash):
        return templates.TemplateResponse(
            "pages/profile.html",
            {"request": request, "user": user, "version": settings.app_version,
             "error": "Aktuelles Passwort falsch"},
            status_code=200,
        )
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "pages/profile.html",
            {"request": request, "user": user, "version": settings.app_version,
             "error": "Passwörter stimmen nicht überein"},
            status_code=400,
        )
    user.password_hash = hash_password(new_password)
    db.commit()
    return RedirectResponse("/profile", status_code=302)


# ── Onboarding Wizard ─────────────────────────────────────────────────────────

def _onboarding_ctx(request: Request, user, step: int, **extra):
    return {"request": request, "user": user, "version": settings.app_version,
            "step": step, **extra}


@router.get("/onboarding/step1", response_class=HTMLResponse)
def onboarding_step1(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    return templates.TemplateResponse(
        "pages/onboarding.html",
        _onboarding_ctx(request, user, 1, tenant=tenant),
    )


@router.post("/onboarding/step1")
def onboarding_step1_submit(
    request: Request,
    org_name: str = Form(...),
    currency: str = Form("EUR"),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if tenant:
        tenant.name = org_name
        tenant.currency = currency
        db.commit()
    return RedirectResponse("/onboarding/step2", status_code=302)


@router.get("/onboarding/step2", response_class=HTMLResponse)
def onboarding_step2(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        "pages/onboarding.html",
        _onboarding_ctx(request, user, 2),
    )


@router.post("/onboarding/step2")
def onboarding_step2_submit(
    request: Request,
    name: str = Form(""),
    provider: str = Form(""),
    cost: float = Form(0.0),
    billing_cycle: str = Form("monthly"),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if name.strip():
        sub = Subscription(
            tenant_id=user.tenant_id,
            created_by_id=user.id,
            name=name,
            provider=provider,
            cost=cost,
            billing_cycle=billing_cycle,
        )
        db.add(sub)
        db.commit()
    return RedirectResponse("/onboarding/step3", status_code=302)


@router.get("/onboarding/step3", response_class=HTMLResponse)
def onboarding_step3(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        "pages/onboarding.html",
        _onboarding_ctx(request, user, 3),
    )


@router.post("/onboarding/complete")
def onboarding_complete(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return RedirectResponse("/dashboard", status_code=302)


# ── Search ───────────────────────────────────────────────────────────────────

@router.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = "", db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    from app.services.search_service import init_fts
    from app.services.search_service import search as fts_search
    init_fts(db)
    results = fts_search(db, user.tenant_id, q) if q else []
    return templates.TemplateResponse(
        "pages/search.html",
        {"request": request, "user": user, "version": settings.app_version,
         "query": q, "results": results},
    )


# ── Import / Export Web ───────────────────────────────────────────────────────

@router.get("/import", response_class=HTMLResponse)
def import_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        "pages/import.html",
        {"request": request, "user": user, "version": settings.app_version},
    )


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request, db: Session = Depends(get_db)):
    from app.services.analytics_service import AnalyticsService
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if user.role != "admin":
        return RedirectResponse("/dashboard", status_code=302)
    summary = AnalyticsService.summary(db, tenant_id=user.tenant_id)
    mrr_history = AnalyticsService.mrr_history(db, tenant_id=user.tenant_id, months=6)
    return templates.TemplateResponse(
        "pages/analytics.html",
        {
            "request": request,
            "user": user,
            "version": settings.app_version,
            "summary": summary,
            "mrr_history": mrr_history,
        },
    )


# ── Audit Log ─────────────────────────────────────────────────────────────────

@router.get("/audit", response_class=HTMLResponse)
def audit_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if user.role != "admin":
        return RedirectResponse("/dashboard", status_code=302)
    entries = AuditService.list(db, tenant_id=user.tenant_id, limit=200)
    return templates.TemplateResponse(
        "pages/audit.html",
        {"request": request, "user": user, "version": settings.app_version, "entries": entries},
    )


# ── Accounts (Konten) ────────────────────────────────────────────────────────

@router.get("/accounts", response_class=HTMLResponse)
def accounts_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    accounts = db.query(Account).filter(Account.tenant_id == user.tenant_id, Account.is_active == True).order_by(Account.name).all()
    from sqlalchemy import func
    total = db.query(func.coalesce(func.sum(Account.balance), 0.0)).filter(
        Account.tenant_id == user.tenant_id, Account.is_active == True
    ).scalar()
    return templates.TemplateResponse(
        "pages/accounts.html",
        {"request": request, "user": user, "version": settings.app_version, "accounts": accounts, "total_balance": float(total)},
    )


@router.get("/accounts/new", response_class=HTMLResponse)
def new_account(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        "pages/account_form.html",
        {"request": request, "user": user, "version": settings.app_version, "account": None},
    )


@router.post("/accounts/new")
def create_account_web(
    request: Request,
    name: str = Form(...),
    type: str = Form("checking"),
    bank_name: str = Form(""),
    balance: float = Form(0.0),
    currency: str = Form("EUR"),
    interest_rate: float = Form(0.0),
    is_primary: str = Form("false"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    acc = Account(
        tenant_id=user.tenant_id,
        created_by_id=user.id,
        name=name,
        type=type,
        bank_name=bank_name,
        balance=balance,
        currency=currency,
        interest_rate=interest_rate,
        is_primary=is_primary == "true",
        notes=notes or None,
    )
    db.add(acc)
    db.commit()
    return RedirectResponse("/accounts", status_code=302)


@router.get("/accounts/{acc_id}/edit", response_class=HTMLResponse)
def edit_account(acc_id: str, request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    acc = db.query(Account).filter(Account.id == acc_id, Account.tenant_id == user.tenant_id).first()
    if not acc:
        return RedirectResponse("/accounts", status_code=302)
    return templates.TemplateResponse(
        "pages/account_form.html",
        {"request": request, "user": user, "version": settings.app_version, "account": acc},
    )


@router.post("/accounts/{acc_id}/edit")
def update_account_web(
    acc_id: str,
    request: Request,
    name: str = Form(...),
    type: str = Form("checking"),
    bank_name: str = Form(""),
    balance: float = Form(0.0),
    currency: str = Form("EUR"),
    interest_rate: float = Form(0.0),
    is_primary: str = Form("false"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    acc = db.query(Account).filter(Account.id == acc_id, Account.tenant_id == user.tenant_id).first()
    if not acc:
        return RedirectResponse("/accounts", status_code=302)
    acc.name = name
    acc.type = type
    acc.bank_name = bank_name
    acc.balance = balance
    acc.currency = currency
    acc.interest_rate = interest_rate
    acc.is_primary = is_primary == "true"
    acc.notes = notes or None
    db.commit()
    return RedirectResponse("/accounts", status_code=302)


@router.post("/accounts/{acc_id}/delete")
def delete_account_web(acc_id: str, request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    acc = db.query(Account).filter(Account.id == acc_id, Account.tenant_id == user.tenant_id).first()
    if acc:
        db.delete(acc)
        db.commit()
    return RedirectResponse("/accounts", status_code=302)


# ── Standing Orders ─────────────────────────────────────────────────

@router.get("/standing-orders", response_class=HTMLResponse)
def standing_orders_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    orders = db.query(StandingOrder).filter(StandingOrder.tenant_id == user.tenant_id, StandingOrder.is_active == True).order_by(StandingOrder.type, StandingOrder.name).all()
    income = [o for o in orders if o.type == "income"]
    expense = [o for o in orders if o.type == "expense"]
    savings = [o for o in orders if o.type == "savings_transfer"]
    return templates.TemplateResponse("pages/standing_orders.html", {
        "request": request, "user": user, "version": settings.app_version,
        "income": income, "expense": expense, "savings": savings, "total": len(orders),
    })


# ── Direct Debits ──────────────────────────────────────────────────

@router.get("/direct-debits", response_class=HTMLResponse)
def direct_debits_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    debits = db.query(DirectDebit).filter(DirectDebit.tenant_id == user.tenant_id, DirectDebit.is_active == True).order_by(DirectDebit.name).all()
    total = sum(d.amount for d in debits)
    return templates.TemplateResponse("pages/direct_debits.html", {
        "request": request, "user": user, "version": settings.app_version,
        "debits": debits, "total_monthly": total,
    })


# ── Investments ────────────────────────────────────────────────────

@router.get("/investments", response_class=HTMLResponse)
def investments_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    investments = db.query(Investment).filter(Investment.tenant_id == user.tenant_id, Investment.is_active == True).order_by(Investment.name).all()
    total_value = sum(i.current_value for i in investments)
    total_invested = sum(i.invested_amount for i in investments)
    return templates.TemplateResponse("pages/investments.html", {
        "request": request, "user": user, "version": settings.app_version,
        "investments": investments, "total_value": total_value, "total_invested": total_invested,
        "total_gain": total_value - total_invested,
    })


# ── Transactions / Haushaltsbuch ───────────────────────────────────

@router.get("/transactions", response_class=HTMLResponse)
def transactions_page(request: Request, month: str = "", db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    from datetime import date as dt_date
    if not month:
        today = dt_date.today()
        month = f"{today.year}-{today.month:02d}"
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    date_from = f"{year}-{mon:02d}-01"
    date_to = f"{year}-{mon+1:02d}-01" if mon < 12 else f"{year+1}-01-01"
    txs = db.query(Transaction).filter(
        Transaction.tenant_id == user.tenant_id,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date < date_to,
    ).order_by(Transaction.transaction_date.desc()).all()
    income = sum(t.amount for t in txs if t.type == "income")
    expense = sum(t.amount for t in txs if t.type == "expense")
    return templates.TemplateResponse("pages/transactions.html", {
        "request": request, "user": user, "version": settings.app_version,
        "transactions": txs, "month": month, "income": income, "expense": expense,
    })


# ── Savings Goals ──────────────────────────────────────────────────

@router.get("/savings-goals", response_class=HTMLResponse)
def savings_goals_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    goals = db.query(SavingsGoal).filter(SavingsGoal.tenant_id == user.tenant_id, SavingsGoal.is_active == True).order_by(SavingsGoal.type).all()
    return templates.TemplateResponse("pages/savings_goals.html", {
        "request": request, "user": user, "version": settings.app_version, "goals": goals,
    })


# ── Retirement ─────────────────────────────────────────────────────

@router.get("/retirement", response_class=HTMLResponse)
def retirement_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    profile = db.query(RetirementProfile).filter(RetirementProfile.user_id == user.id).first()
    if not profile:
        profile = RetirementProfile(tenant_id=user.tenant_id, user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    from app.services.retirement import RetirementService
    calc = RetirementService.calculate(
        current_age=profile.current_age, retirement_age=profile.retirement_age,
        life_expectancy=profile.life_expectancy, desired_monthly_income=profile.desired_monthly_income,
        expected_pension=profile.expected_pension, current_savings=profile.current_savings,
        expected_return_pct=profile.expected_return_pct,
    )
    return templates.TemplateResponse("pages/retirement.html", {
        "request": request, "user": user, "version": settings.app_version,
        "profile": profile, "calc": calc,
    })


# ── Budget Alerts ──────────────────────────────────────────────────

@router.get("/budget-alerts", response_class=HTMLResponse)
def budget_alerts_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    alerts = db.query(BudgetAlert).filter(BudgetAlert.tenant_id == user.tenant_id, BudgetAlert.is_active == True).order_by(BudgetAlert.name).all()
    return templates.TemplateResponse("pages/budget_alerts.html", {
        "request": request, "user": user, "version": settings.app_version, "alerts": alerts,
    })


# ── Berichte ─────────────────────────────────────────────────────────────────

@router.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    from datetime import date
    today = date.today()
    # Build last 3 months for quick access
    recent_months = []
    y, m = today.year, today.month
    for _ in range(3):
        recent_months.append({"year": y, "month": m})
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return templates.TemplateResponse("pages/reports.html", {
        "request": request, "user": user, "version": settings.app_version,
        "current_year": today.year, "current_month": today.month,
        "recent_months": recent_months,
    })


# ── Auto-Buchungen ────────────────────────────────────────────────────────────

@router.get("/bookings", response_class=HTMLResponse)
def bookings_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    from datetime import date
    today = date.today()
    return templates.TemplateResponse("pages/bookings.html", {
        "request": request, "user": user, "version": settings.app_version,
        "current_year": today.year, "current_month": today.month,
    })


# ── Cashflow Dashboard ──────────────────────────────────────────────

@router.get("/cashflow", response_class=HTMLResponse)
def cashflow_dashboard(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    summary = CashflowService.monthly_summary(db, tenant_id=user.tenant_id)

    # Net worth
    from sqlalchemy import func
    accounts_total = db.query(func.coalesce(func.sum(Account.balance), 0.0)).filter(
        Account.tenant_id == user.tenant_id, Account.is_active == True
    ).scalar()
    investments_total = db.query(func.coalesce(func.sum(Investment.current_value), 0.0)).filter(
        Investment.tenant_id == user.tenant_id, Investment.is_active == True
    ).scalar()
    savings_goals = db.query(SavingsGoal).filter(
        SavingsGoal.tenant_id == user.tenant_id, SavingsGoal.is_active == True
    ).all()

    return templates.TemplateResponse(
        "pages/cashflow.html",
        {
            "request": request,
            "user": user,
            "version": settings.app_version,
            "summary": summary,
            "accounts_total": float(accounts_total),
            "investments_total": float(investments_total),
            "net_worth": float(accounts_total) + float(investments_total),
            "savings_goals": savings_goals,
        },
    )


# ── Cashflow Calendar ───────────────────────────────────────────────

@router.get("/cashflow/calendar", response_class=HTMLResponse)
def cashflow_calendar_page(request: Request, month: str = "2026-03", db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    import calendar as cal
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    num_days = cal.monthrange(year, mon)[1]

    standing_orders = db.query(StandingOrder).filter(
        StandingOrder.tenant_id == user.tenant_id, StandingOrder.is_active == True
    ).all()
    direct_debits = db.query(DirectDebit).filter(
        DirectDebit.tenant_id == user.tenant_id, DirectDebit.is_active == True
    ).all()

    days = []
    running = 0.0
    for d in range(1, num_days + 1):
        entries = []
        for so in standing_orders:
            if so.execution_day == d:
                etype = "income" if so.type == "income" else "expense"
                entries.append({"name": so.name, "amount": so.amount, "type": etype})
                running += so.amount if so.type == "income" else -so.amount
        for dd in direct_debits:
            if dd.expected_day == d:
                entries.append({"name": dd.name, "amount": dd.amount, "type": "expense"})
                running -= dd.amount
        days.append({"day": d, "entries": entries, "running_balance": round(running, 2)})

    prev_mon = mon - 1 if mon > 1 else 12
    prev_year = year if mon > 1 else year - 1
    next_mon = mon + 1 if mon < 12 else 1
    next_year = year if mon < 12 else year + 1

    return templates.TemplateResponse("pages/cashflow_calendar.html", {
        "request": request, "user": user, "version": settings.app_version,
        "month": month, "days": days, "num_days": num_days,
        "month_name": cal.month_name[mon],
        "prev_month": f"{prev_year}-{prev_mon:02d}",
        "next_month": f"{next_year}-{next_mon:02d}",
    })


# ── Cashflow Simulator ──────────────────────────────────────────────

@router.get("/cashflow/simulator", response_class=HTMLResponse)
def cashflow_simulator_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    summary = CashflowService.monthly_summary(db, tenant_id=user.tenant_id)
    return templates.TemplateResponse("pages/cashflow_simulator.html", {
        "request": request, "user": user, "version": settings.app_version,
        "summary": summary,
    })


# ── Cashflow Onboarding Wizard (6 Steps) ────────────────────────────

def _cf_onboarding_ctx(request, user, step, **extra):
    return {"request": request, "user": user, "version": settings.app_version, "step": step, **extra}


def _get_primary_account(db, tenant_id):
    acc = db.query(Account).filter(Account.tenant_id == tenant_id, Account.is_primary == True).first()
    if not acc:
        acc = db.query(Account).filter(Account.tenant_id == tenant_id).first()
    return acc


@router.get("/cashflow-onboarding/step1", response_class=HTMLResponse)
def cf_onboarding_step1(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("pages/cashflow_onboarding.html", _cf_onboarding_ctx(request, user, 1))


@router.post("/cashflow-onboarding/step1")
def cf_onboarding_step1_submit(
    request: Request,
    account_name: str = Form(...),
    account_type: str = Form("checking"),
    bank_name: str = Form(""),
    balance: float = Form(0.0),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    acc = Account(
        tenant_id=user.tenant_id, created_by_id=user.id,
        name=account_name, type=account_type, bank_name=bank_name,
        balance=balance, is_primary=True,
    )
    db.add(acc)
    db.commit()
    return RedirectResponse("/cashflow-onboarding/step2", status_code=302)


@router.get("/cashflow-onboarding/step2", response_class=HTMLResponse)
def cf_onboarding_step2(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("pages/cashflow_onboarding.html", _cf_onboarding_ctx(request, user, 2))


@router.post("/cashflow-onboarding/step2")
def cf_onboarding_step2_submit(
    request: Request,
    gehalt_amount: float = Form(0.0),
    miete_amount: float = Form(0.0),
    versicherung_amount: float = Form(0.0),
    kfz_amount: float = Form(0.0),
    sparplan_amount: float = Form(0.0),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    acc = _get_primary_account(db, user.tenant_id)
    acc_id = acc.id if acc else None

    orders = []
    if gehalt_amount > 0:
        orders.append(("Gehalt", "income", gehalt_amount, 27))
    if miete_amount > 0:
        orders.append(("Miete", "expense", miete_amount, 1))
    if versicherung_amount > 0:
        orders.append(("Versicherung", "expense", versicherung_amount, 1))
    if kfz_amount > 0:
        orders.append(("KFZ-Versicherung", "expense", kfz_amount, 1))
    if sparplan_amount > 0:
        orders.append(("Sparplan", "savings_transfer", sparplan_amount, 1))

    for name, so_type, amount, day in orders:
        so = StandingOrder(
            tenant_id=user.tenant_id, created_by_id=user.id, account_id=acc_id,
            name=name, type=so_type, amount=amount, frequency="monthly", execution_day=day,
        )
        db.add(so)
    if orders:
        db.commit()
    return RedirectResponse("/cashflow-onboarding/step3", status_code=302)


@router.get("/cashflow-onboarding/step3", response_class=HTMLResponse)
def cf_onboarding_step3(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("pages/cashflow_onboarding.html", _cf_onboarding_ctx(request, user, 3))


@router.post("/cashflow-onboarding/step3")
def cf_onboarding_step3_submit(
    request: Request,
    strom_amount: float = Form(0.0),
    gas_amount: float = Form(0.0),
    internet_amount: float = Form(0.0),
    gez_amount: float = Form(0.0),
    fitness_amount: float = Form(0.0),
    handy_amount: float = Form(0.0),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    acc = _get_primary_account(db, user.tenant_id)
    acc_id = acc.id if acc else None

    debits = [
        ("Strom", strom_amount, 5),
        ("Gas", gas_amount, 5),
        ("Internet", internet_amount, 3),
        ("GEZ/Rundfunk", gez_amount, 15),
        ("Fitnessstudio", fitness_amount, 1),
        ("Handy", handy_amount, 10),
    ]
    for name, amount, day in debits:
        if amount > 0:
            dd = DirectDebit(
                tenant_id=user.tenant_id, created_by_id=user.id, account_id=acc_id,
                name=name, amount=amount, frequency="monthly", expected_day=day,
            )
            db.add(dd)
    db.commit()
    return RedirectResponse("/cashflow-onboarding/step4", status_code=302)


@router.get("/cashflow-onboarding/step4", response_class=HTMLResponse)
def cf_onboarding_step4(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("pages/cashflow_onboarding.html", _cf_onboarding_ctx(request, user, 4))


@router.post("/cashflow-onboarding/step4")
def cf_onboarding_step4_submit(
    request: Request,
    etf_value: float = Form(0.0),
    etf_invested: float = Form(0.0),
    tagesgeld_value: float = Form(0.0),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if etf_value > 0:
        from app.models.investment import Investment as Inv
        inv = Inv(
            tenant_id=user.tenant_id, created_by_id=user.id,
            name="ETF-Sparplan", type="etf",
            current_value=etf_value, invested_amount=etf_invested or etf_value,
        )
        db.add(inv)
    if tagesgeld_value > 0:
        from app.models.investment import Investment as Inv
        inv = Inv(
            tenant_id=user.tenant_id, created_by_id=user.id,
            name="Tagesgeld", type="other",
            current_value=tagesgeld_value, invested_amount=tagesgeld_value,
        )
        db.add(inv)
    db.commit()
    return RedirectResponse("/cashflow-onboarding/step5", status_code=302)


@router.get("/cashflow-onboarding/step5", response_class=HTMLResponse)
def cf_onboarding_step5(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("pages/cashflow_onboarding.html", _cf_onboarding_ctx(request, user, 5))


@router.post("/cashflow-onboarding/step5")
def cf_onboarding_step5_submit(
    request: Request,
    notgroschen_target: float = Form(0.0),
    notgroschen_current: float = Form(0.0),
    urlaub_target: float = Form(0.0),
    urlaub_current: float = Form(0.0),
    rente_target: float = Form(0.0),
    rente_current: float = Form(0.0),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    goals = [
        ("Notgroschen", "emergency", notgroschen_target, notgroschen_current),
        ("Urlaub / Luxus", "vacation_luxury", urlaub_target, urlaub_current),
        ("Rente", "retirement", rente_target, rente_current),
    ]
    for name, goal_type, target, current in goals:
        if target > 0:
            sg = SavingsGoal(
                tenant_id=user.tenant_id, created_by_id=user.id,
                name=name, type=goal_type,
                target_amount=target, current_amount=current,
            )
            db.add(sg)
    db.commit()
    return RedirectResponse("/cashflow-onboarding/step6", status_code=302)


@router.get("/cashflow-onboarding/step6", response_class=HTMLResponse)
def cf_onboarding_step6(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    tid = user.tenant_id
    summary = CashflowService.monthly_summary(db, tenant_id=tid)
    return templates.TemplateResponse("pages/cashflow_onboarding.html", _cf_onboarding_ctx(
        request, user, 6,
        account_count=db.query(Account).filter(Account.tenant_id == tid).count(),
        standing_order_count=db.query(StandingOrder).filter(StandingOrder.tenant_id == tid).count(),
        direct_debit_count=db.query(DirectDebit).filter(DirectDebit.tenant_id == tid).count(),
        investment_count=db.query(Investment).filter(Investment.tenant_id == tid).count(),
        savings_goal_count=db.query(SavingsGoal).filter(SavingsGoal.tenant_id == tid).count(),
        summary=summary,
    ))


@router.post("/cashflow-onboarding/complete")
def cf_onboarding_complete(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return RedirectResponse("/cashflow", status_code=302)
