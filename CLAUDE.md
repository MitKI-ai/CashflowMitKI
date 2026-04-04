# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**cashflow.mitKI.ai** — Multi-Tenant SaaS Cashflow & Retirement Planner by mitKI.ai.
FastAPI Python monolith with Jinja2 SSR frontend. Live at **https://www.cashflow.mitki.ai**.
Deployed on Container 110 (192.168.1.17:8080) via systemd + uvicorn. Prefect (CT109) handles background jobs.

**Demo login:** `admin@mitki.ai` / `admin123` (after `python scripts/seed.py`)
**Cashflow demo:** `markus@demo.com` / `demo1234` (after `python scripts/seed_cashflow.py`)

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Seed database
python scripts/seed.py           # Admin-User + Subscriptions
python scripts/seed_cashflow.py  # Cashflow Demo-Daten (Markus, 38, Familienvater)

# Run development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Run with Docker
docker compose up

# Run unit/integration tests
pytest tests/ --ignore=tests/e2e -v

# Run E2E tests (Playwright)
pytest tests/e2e/ -v --headed    # mit sichtbarem Browser
pytest tests/e2e/ -v             # headless (CI)

# Lint
ruff check app/ tests/
```

## Deploy to Production (CT110)

```bash
# 1. Tar bauen (Windows)
tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='tests' --exclude='test.db' --exclude='.env' \
    --exclude='venv' --exclude='data' -czf /tmp/abo-manager.tar.gz .

# 2. Auf Proxmox + CT110 übertragen
scp /tmp/abo-manager.tar.gz aiworker@prox.mox:/tmp/
ssh aiworker@prox.mox "sudo pct push 110 /tmp/abo-manager.tar.gz /tmp/abo-manager.tar.gz && \
  sudo pct exec 110 -- bash -c 'cd /home/aiworker/abo-manager && tar -xzf /tmp/abo-manager.tar.gz --overwrite'"

# 3. Dependencies + Restart
ssh aiworker@prox.mox "sudo pct exec 110 -- bash -c \
  'cd /home/aiworker/abo-manager && venv/bin/pip install -r requirements.txt -q && systemctl restart abo-manager'"
```

## Architecture

### Request Flow

```
Browser / API Client
  → Web Routes (app/web/routes/pages.py)  — HTML responses via Jinja2
  → API Routes (app/api/v1/)              — JSON responses
  → GraphQL (app/graphql/schema.py)       — Strawberry at /graphql
    → Dependencies (app/dependencies.py)  — auth + tenant context
      → Services (app/services/)          — business logic
        → SQLAlchemy Session (app/database.py)
          → Models (app/models/)
```

### Multi-Tenancy

Every tenant-scoped model has a `tenant_id` FK. **All queries must filter by `tenant_id`** — this is the only isolation mechanism. Use `get_current_tenant_id()` dependency in every endpoint that touches tenant data. The `require_role()` dependency enforces RBAC on top.

### Authentication

Dual-mode: `get_current_user()` in `app/dependencies.py` checks Bearer JWT first, then falls back to session cookie. Password hashing uses `bcrypt` directly (not passlib — incompatible with Python 3.14). SSO via Google + Microsoft OAuth2 (authlib).

**Session-Cookie Hinweis:** `IS_PRODUCTION=false` in `.env` auf CT110 setzen — Cloudflare terminiert TLS, Caddy leitet HTTP intern weiter, daher kein `Secure`-Cookie nötig.

### Key Design Choices

- **Dual Auth** — `get_current_user()` checks Bearer JWT first, then session cookie. JWT via `app/core/jwt.py` (HS256, PyJWT).
- **No APScheduler in-process** — Background jobs go to Prefect (CT109, 192.168.1.16:4200). Work pool: `subscription-manager`.
- **SQLite with WAL mode** — enabled on connect in `database.py` for concurrency.
- **Alembic** — `render_as_batch=True` for SQLite ALTER TABLE support. Migrations in `migrations/`.
- **structlog** — JSON logging in production, ConsoleRenderer in dev. Configured in `app/core/logging.py`.
- **GraphQL** — Strawberry at `/graphql` with Query + Mutation (`app/graphql/schema.py`).
- **Playwright E2E** — Tests in `tests/e2e/` with own `conftest.py` (overrides `reset_db`, starts real uvicorn server on port 8765).
- **IBAN/Finanzdaten** — Never log amounts or IBANs. Exclude from standard API responses.
- **NocoDB** (Container 106) is used for Icon Library admin, not as app database.
- **reportlab** — PDF generation for monthly reports (pure Python, no binary deps).
- **Fernet encryption** — API keys for LLM providers encrypted with SHA256-derived key from APP_SECRET_KEY.

### File Layout

```
app/
  main.py            — FastAPI app, lifespan, middleware (RequestID, Security, CORS)
  config.py          — Pydantic-Settings from .env (app_base_url, smtp_from, etc.)
  database.py        — SQLAlchemy engine, Base, get_db()
  dependencies.py    — get_current_user, get_current_tenant_id, require_role()
  models/            — SQLAlchemy ORM (one file per entity)
  schemas/           — Pydantic request/response models
  services/          — Business logic
    cashflow.py      — CashflowService (monthly summary)
    retirement.py    — RetirementService (PMT formula, 3 scenarios)
    booking_service.py — Auto-Buchungen aus Daueraufträgen + DirectDebits
    report_service.py  — PDF Finanzreport (ReportLab)
    llm_service.py   — LLM chat (Anthropic SDK + OpenRouter)
    bank_import.py   — PDF/CSV Kontoauszug Import
    email_service.py — SMTP + Jinja2 templates
  api/v1/            — JSON REST endpoints
    bookings.py      — Auto-Buchungen (pending, confirm, generate-for-month)
    reports.py       — PDF Download + E-Mail
    llm.py           — LLM Provider CRUD + Chat
    bank_import.py   — Kontoauszug Import
    cashflow.py      — Cashflow Summary, Simulator, Kalender, Snapshots
    retirement.py    — Renten-Rechner + Szenarien
    widgets.py       — Dashboard Widget Registry + Config
    internal.py      — Prefect-interne Endpoints (X-Internal-Key)
  api/health.py      — /health and /metrics (no auth required)
  web/routes/        — Jinja2 SSR page routes
  core/
    security.py      — bcrypt hash/verify
    jwt.py           — JWT create/decode (HS256)
    logging.py       — structlog configuration
    i18n.py          — DE+EN translations
    encryption.py    — Fernet encrypt/decrypt für API-Keys
  graphql/schema.py  — Strawberry GraphQL
  templates/         — Jinja2 HTML (base.html + pages/)
tests/               — 479 Tests (unit + integration), --ignore=tests/e2e für CI
flows/               — Prefect Flows (renewal_reminder, auto_renewal, monthly_report)
scripts/
  seed.py            — Demo data (admin@mitki.ai / admin123)
  seed_cashflow.py   — Cashflow Demo-Daten (markus@demo.com / demo1234)
migrations/          — Alembic (render_as_batch=True)
```

### Infrastructure (Proxmox)

| What | Where |
|------|-------|
| App runs | Container 110 · 192.168.1.17:8080 · systemd: abo-manager.service |
| Reverse Proxy | Container 104 · Caddy + Cloudflare Tunnel (mitki-proxy) |
| Prefect | Container 109 · 192.168.1.16:4200 · automatisch.mitki.ai |
| NocoDB | Container 106 · nocodb.mitki.ai |
| Coolify | Container 111 · coolify.mitki.ai |
| Proxmox Host | prox.mox · SSH: aiworker@prox.mox |
| External domain | **www.cashflow.mitki.ai** + **cashflow.mitki.ai** (CF Tunnel) |

## PRD & Backlog

- **Subscription Manager PRD (v2.0):** `docs/prd-subscription-manager-2026-03-27.md` — Sprint 1-9, 230 Punkte ✅
- **Cashflow Planner PRD (v4.0):** `docs/prd-cashflow-planner-2026-03-30.md` — Sprint 10-20, 239 Punkte ✅
- **Sprint-Status:** `.bmad/sprint-status.yaml` — 20 Sprints, 469 Punkte, 107 Stories, 479 Tests

### Implementierte Epics (Sprint 10–20)
- EPIC-100–106: Cashflow-Kern (Konten, Daueraufträge, Haushaltsbuch, Rente, Onboarding)
- EPIC-202: Inflationsbereinigung + 3-Szenarien-Renten-Rechner
- EPIC-205: Dashboard Widget-System (8 Widgets, 3 Presets, Drag & Drop)
- EPIC-206: LLM Chat Assistant (Anthropic + OpenRouter, 11 Tools, CRUD aller Entities)
- EPIC-207: Smart Bank Statement Import (PDF+CSV, Fuzzy-Matching, LLM-Kategorisierung)
- EPIC-208: PDF Finanzreport (ReportLab, /reports Seite, E-Mail, Prefect-Flow)
- EPIC-212: Auto-Buchungen (BookingService, Duplicate-Detection, Confirm-UI)

### Offene Epics (vorgeschlagen)
- EPIC-209: Multi-Währung & FX-Rates (~26 Punkte)
- EPIC-210: Partner-Modus / Haushalt teilen (~21 Punkte)
- EPIC-211: Mobile PWA (~18 Punkte)
- EPIC-213: PostgreSQL Migration (~21 Punkte)

### All Cashflow Entities

```
Account → StandingOrder, DirectDebit, Transaction, Investment
Transfer (Account ↔ Account)
SavingsGoal (3 Typen: emergency, vacation_luxury, retirement)
RetirementProfile (1:1 pro User)
CashflowSnapshot (monatlich, Prefect)
BudgetAlert, LLMProvider, ImportHistory, WidgetConfig

Cashflow = Σ StandingOrders(income)
         - Σ StandingOrders(expense)
         - Σ DirectDebits
         - Σ Subscriptions (bestehend)
         - Σ Transactions(expense)
```
