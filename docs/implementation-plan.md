# Subscription Manager — Vision & Implementierungsplan

## Context

Der Subscription Manager soll ein SaaS-Produkt für mitKI.ai werden — gleichzeitig echtes Produkt und YouTube-Showcase. Aktuell existiert **kein Application-Code** — nur Branding-Docs und ein Demo-Repo. Alles muss von Grund auf gebaut werden.

Die Vision wurde durch 50 J/N-Fragen definiert. Der Tech-Stack steht fest: **FastAPI + Jinja2 SSR + Tailwind CSS + SQLite + Docker + Coolify auf Proxmox**.

---

## Aktueller Stand

| Was | Status |
|-----|--------|
| Application-Code | Nicht vorhanden |
| Dockerfile | Nicht vorhanden |
| CI/CD Pipeline | Nicht vorhanden |
| Datenbank | Nicht vorhanden |
| Tests | Nicht vorhanden |
| Coolify-Config | Nicht vorhanden |
| Branding-Docs | branding.md vorhanden |

---

## Projektstruktur

```
subscription-manager/
├── .github/workflows/ci.yml
├── app/
│   ├── main.py              # FastAPI App + Lifespan
│   ├── config.py             # Pydantic-Settings
│   ├── database.py           # SQLAlchemy Engine + Session
│   ├── dependencies.py       # get_db, get_current_user, get_current_tenant
│   ├── models/               # SQLAlchemy ORM (tenant, user, subscription, plan, ...)
│   ├── schemas/              # Pydantic Request/Response Models
│   ├── api/v1/               # REST API Routen
│   ├── web/routes/           # Jinja2 SSR Seiten
│   ├── services/             # Business Logic (kein HTTP)
│   ├── core/                 # Security, Middleware, i18n, Events
│   └── templates/            # Jinja2 HTML + Email-Templates
├── static/                   # CSS, JS, Images
├── translations/             # de.json, en.json
├── migrations/               # Alembic
├── tests/                    # pytest
├── data/                     # SQLite Mount-Point
├── scripts/                  # seed.py, create_admin.py
├── Dockerfile
├── docker-compose.yml
├── docker-compose.staging.yml
├── docker-compose.prod.yml
├── .env.example
├── pyproject.toml
├── requirements.txt
└── alembic.ini
```

---

## CI/CD Pipeline

```
Feature-Branch → PR → staging Branch → Coolify Staging (8081)
                                    ↓
                  staging → PR → main Branch → Coolify Production (8080)
```

**GitHub Actions** (`ci.yml`):
1. `ruff check` (Linting)
2. `mypy` (Type-Checking)
3. `pytest` mit Coverage
4. Docker Build (nur auf main/staging)

**Coolify**:
- 2 Apps: "SubManager-Staging" (Branch: `staging`, Port: 8081) + "SubManager-Production" (Branch: `main`, Port: 8080)
- Auto-Deploy bei Push auf jeweiligen Branch
- Health-Check: `GET /health`
- Separate Volumes für `/data` (isolierte SQLite-DBs)
- Environment-Variablen pro App in Coolify-UI

---

## Datenbank-Schema (MVP)

**Kern-Entities**: Tenant → Users, Subscriptions, Plans, Categories, AuditLog, Notifications, WebhookEndpoints, Coupons

- Alle IDs: TEXT (UUID) — funktioniert identisch in SQLite und PostgreSQL
- Multi-Tenancy: `tenant_id` FK auf jeder Tenant-scoped Tabelle
- JSON-Felder als TEXT (→ JSONB bei PostgreSQL-Migration)
- FTS5 für Volltextsuche (→ tsvector bei PostgreSQL)

---

## Phasenplan

### Phase 1 — MVP (Wochen 1-6)
**Sprint 1** (W1-2): Projekt-Skeleton, Auth, Tenant/User Models, `/health`, Dockerfile, Coolify-Deploy
**Sprint 2** (W3-4): Subscription/Plan CRUD, Dashboard mit Charts, API, Responsive Layout
**Sprint 3** (W5-6): E-Mail Notifications (APScheduler), In-App Notifications, Audit Log, Auto-Renewal

### Phase 2 — Self-Service & Teams (Wochen 7-10)
**Sprint 4** (W7-8): RBAC, Teams/Orga, Onboarding Wizard, User Management
**Sprint 5** (W9-10): Import/Export, Volltextsuche, i18n (DE+EN)

### Phase 3 — Integrationen (Wochen 11-14)
**Sprint 6** (W11-12): Webhooks, Coupons, Custom Fields
**Sprint 7** (W13-14): Admin Analytics Dashboard, Health/Metrics, Structured Logging

### Phase 4 — Security Upgrade (Wochen 15-18)
**Sprint 8** (W15-16): OAuth2/JWT, SSO (Google, Microsoft)
**Sprint 9** (W17-18): GraphQL API (Strawberry)

### Phase 5 — Launch (Wochen 19-22)
**Sprint 10** (W19-20): UX Polish, YouTube Demo-Daten, Landing Page
**Sprint 11** (W21-22): PostgreSQL-Migration testen, Security Review, Grafana/Loki Setup

---

## MCP Tools Empfehlung

| MCP Server | Zweck | Wann |
|---|---|---|
| **GitHub MCP** | Issues, PRs, CI-Status direkt aus Claude Code | Sofort |
| **SQLite MCP** | DB inspizieren, Queries testen | Ab Sprint 1 |
| **Fetch MCP** | API-Endpoints testen, Health-Checks | Ab Sprint 1 |
| **Docker MCP** | Container bauen, Logs ansehen | Ab Sprint 2 |
| **PostgreSQL MCP** | DB-Migration validieren | Phase 5 |

---

## Verifikation

Nach Sprint 1 Abschluss prüfen:
1. `docker compose up` → Container startet ohne Fehler
2. `curl http://localhost:8080/health` → `{"status": "ok"}`
3. Login-Seite unter `http://localhost:8080/login` erreichbar
4. `pytest tests/ -v` → alle Tests grün
5. Git Push → Coolify baut automatisch → Health-Check grün
