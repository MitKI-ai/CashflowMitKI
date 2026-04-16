"""Seed script: creates default tenant + admin user + demo data."""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models.category import Category
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.user import User

db = SessionLocal()

# Check if data exists
if db.query(Tenant).first():
    print("Data already exists. Skipping seed.")
    sys.exit(0)

# Tenant
tenant = Tenant(name="mitKI.ai Demo", slug="mitki-demo", plan_tier="pro", currency="EUR", locale="de")
db.add(tenant)
db.flush()

# Admin User
admin = User(
    tenant_id=tenant.id,
    email=settings.admin_email,
    password_hash=hash_password(settings.admin_password),
    display_name="Admin",
    role="admin",
)
db.add(admin)
db.flush()

# Categories
cats = {}
for name, color in [("SaaS", "#F97316"), ("Hosting", "#3B82F6"), ("Tools", "#10B981"), ("Media", "#8B5CF6")]:
    c = Category(tenant_id=tenant.id, name=name, color=color)
    db.add(c)
    db.flush()
    cats[name] = c

# Plans
for name, price, cycle in [("Basic Monthly", 9.99, "monthly"), ("Pro Monthly", 29.99, "monthly"), ("Enterprise Yearly", 299.99, "yearly")]:
    db.add(Plan(tenant_id=tenant.id, name=name, price=price, currency="EUR", billing_cycle=cycle))

# Demo Subscriptions
today = date.today()
demos = [
    ("GitHub Team", "GitHub", 44.00, "monthly", "active", today - timedelta(days=120), today + timedelta(days=5)),
    ("AWS Lightsail", "Amazon", 20.00, "monthly", "active", today - timedelta(days=90), today + timedelta(days=3)),
    ("Slack Business+", "Slack", 12.50, "monthly", "active", today - timedelta(days=60), today + timedelta(days=15)),
    ("Figma Professional", "Figma", 15.00, "monthly", "active", today - timedelta(days=45), today + timedelta(days=22)),
    ("Adobe Creative Cloud", "Adobe", 59.99, "monthly", "paused", today - timedelta(days=200), None),
    ("Notion Team", "Notion", 10.00, "monthly", "active", today - timedelta(days=30), today + timedelta(days=28)),
    ("Zoom Business", "Zoom", 18.99, "monthly", "cancelled", today - timedelta(days=150), None),
    ("Claude Pro", "Anthropic", 20.00, "monthly", "active", today - timedelta(days=15), today + timedelta(days=12)),
    ("Hetzner Cloud", "Hetzner", 4.51, "monthly", "active", today - timedelta(days=365), today + timedelta(days=1)),
    ("1Password Business", "1Password", 7.99, "monthly", "active", today - timedelta(days=80), today + timedelta(days=9)),
]

for name, provider, cost, cycle, status, start, renewal in demos:
    sub = Subscription(
        tenant_id=tenant.id,
        created_by_id=admin.id,
        name=name,
        provider=provider,
        cost=cost,
        currency="EUR",
        billing_cycle=cycle,
        status=status,
        start_date=start,
        next_renewal=renewal,
        auto_renew=status == "active",
    )
    db.add(sub)

db.commit()
print(f"Seed complete: 1 tenant, 1 admin ({settings.admin_email}), {len(demos)} subscriptions, 4 categories, 3 plans")
db.close()
