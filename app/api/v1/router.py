from fastapi import APIRouter

from app.api.v1.accounts import router as accounts_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.direct_debits import router as direct_debits_router
from app.api.v1.standing_orders import router as standing_orders_router
from app.api.v1.transfers import router as transfers_router
from app.api.v1.investments import router as investments_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.savings_goals import router as savings_goals_router
from app.api.v1.cashflow import router as cashflow_router
from app.api.v1.retirement import router as retirement_router
from app.api.v1.budget_alerts import router as budget_alerts_router
from app.api.v1.widgets import router as widgets_router
from app.api.v1.llm import router as llm_router
from app.api.v1.bank_import import router as bank_import_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.reports import router as reports_router
from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.coupons import router as coupons_router
from app.api.v1.custom_fields import router as custom_fields_router
from app.api.v1.icons import router as icons_router
from app.api.v1.import_export import router as import_export_router
from app.api.v1.internal import router as internal_router
from app.api.v1.invitations import router as invitations_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.plans import router as plans_router
from app.api.v1.search import router as search_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.users import router as users_router
from app.api.v1.webhooks import router as webhooks_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(subscriptions_router)
api_v1_router.include_router(plans_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(internal_router)
api_v1_router.include_router(invitations_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(import_export_router)
api_v1_router.include_router(icons_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(coupons_router)
api_v1_router.include_router(custom_fields_router)
api_v1_router.include_router(accounts_router)
api_v1_router.include_router(standing_orders_router)
api_v1_router.include_router(direct_debits_router)
api_v1_router.include_router(transfers_router)
api_v1_router.include_router(investments_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(savings_goals_router)
api_v1_router.include_router(cashflow_router)
api_v1_router.include_router(retirement_router)
api_v1_router.include_router(budget_alerts_router)
api_v1_router.include_router(widgets_router)
api_v1_router.include_router(llm_router)
api_v1_router.include_router(bank_import_router)
api_v1_router.include_router(bookings_router)
api_v1_router.include_router(reports_router)
