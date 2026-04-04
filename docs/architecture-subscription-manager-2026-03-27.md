# Architecture Document: Subscription Manager

**Date:** 2026-03-27
**Author:** Eddy (mitKI.ai)
**Version:** 1.0
**Project Level:** Level 3 (Multi-Tenant SaaS)
**Status:** Approved

**Related Documents:**
- PRD: `docs/prd-subscription-manager-2026-03-27.md`
- Infrastructure: `docs/infrastructure.md`
- Branding: `branding.md`

---

## Executive Summary

Der Subscription Manager ist ein **Layered Modular Monolith** auf Basis von FastAPI (Python). Die Architektur priorisiert:

1. **Simplicity over Premature Scaling** — SQLite + single Docker container sind für den MVP und frühe Growth-Phase ausreichend
2. **Clear Upgrade Paths** — SQLite → PostgreSQL, Session Auth → JWT/OAuth2, APScheduler → Prefect sind als explizite Pfade eingebaut
3. **Multi-Tenancy by Design** — `tenant_id` auf jeder Tabelle, nie optional
4. **SSR-First** — Jinja2 + Vanilla JS für schnelle Time-to-Market, kein Build-Step, kein SPA-Framework

---

## Part 1: Architectural Drivers

Die folgenden NFRs treiben die wichtigsten Architekturentscheidungen:

| Driver | NFR | Architekturentscheidung |
|--------|-----|------------------------|
| **Tenant Isolation** | NFR-006 | `tenant_id` FK auf jeder Tabelle, Dependency `get_current_tenant_id` in jeder Route |
| **Performance** | NFR-001, NFR-002 | SQLite WAL-Mode, indizierte Queries, kein N+1, Chart.js lazy-loaded |
| **Security** | NFR-004, NFR-005 | bcrypt (rounds=12), signed session cookies, HTTPS via Cloudflare |
| **Code Quality** | NFR-010 | ruff + mypy im CI, pre-commit hooks |
| **Availability** | NFR-003 | Docker restart-policy, Health-Check via Coolify, SQLite WAL (kein single writer block) |
| **Concurrency** | NFR-011 | SQLite WAL erlaubt multiple concurrent readers, 50 User = OK |
| **DB Portability** | FR-035 | Alle Queries via SQLAlchemy ORM, FTS5-Code isoliert in `services/search_service.py` |
| **Background Jobs** | FR-010, FR-017 | Prefect (Container 109) statt in-process APScheduler |

---

## Part 2: High-Level Architecture

### Pattern: Layered Modular Monolith

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│           Browser (HTML/Jinja2 SSR + Vanilla JS)                │
│           API Clients (REST /api/v1/)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS via Cloudflare → Caddy (LXC 104)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                           │
│  ┌──────────────────────┐   ┌──────────────────────────────┐   │
│  │  Web Routes (SSR)    │   │  REST API Routes (/api/v1/)  │   │
│  │  app/web/routes/     │   │  app/api/v1/                 │   │
│  │  Jinja2 Templates    │   │  FastAPI + Pydantic Schemas  │   │
│  └──────────┬───────────┘   └──────────────┬───────────────┘   │
│             │                               │                    │
│  SessionMiddleware + require_role() Dependency                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      Service Layer                               │
│  app/services/                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌─────────┐  │
│  │subscription_ │ │notification_ │ │search_     │ │email_   │  │
│  │service.py    │ │service.py    │ │service.py  │ │service.py│  │
│  └──────────────┘ └──────────────┘ └────────────┘ └─────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────┐              │
│  │audit_service │ │webhook_      │ │icon_       │              │
│  │.py           │ │service.py    │ │service.py  │              │
│  └──────────────┘ └──────────────┘ └────────────┘              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                       Data Layer                                 │
│  app/models/ (SQLAlchemy 2.0 ORM)                               │
│  SQLite (WAL mode) → PostgreSQL Migration Path                   │
│  Volume: /data/subscriptions.db                                  │
└─────────────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Prefect     │ │  NocoDB      │ │  SMTP Server  │
│  (LXC 109)   │ │  (LXC 106)   │ │  (extern)    │
│  Background  │ │  Icon Lib    │ │  E-Mail       │
│  Jobs        │ │  Admin UI    │ │  Notifications│
└──────────────┘ └──────────────┘ └──────────────┘
```

### Interaction Summary

```
User → Browser → Cloudflare (TLS) → CF Tunnel → Caddy Proxy (LXC 104)
     → LXC 110: Docker Container (FastAPI :8000) → SQLite /data/
                                                  → Prefect API (LXC 109)
                                                  → NocoDB API (LXC 106)
                                                  → SMTP
```

---

## Part 3: Technology Stack

### Frontend

**Choice:** Jinja2 SSR + Tailwind CSS (CDN) + Vanilla JS

**Rationale:**
- Kein Build-Step, sofort deploybar
- Server-Side Rendering = kein API-Call für initiales Rendering (bessere p95-Latenz)
- Tailwind CDN für MVP-Geschwindigkeit (kann bei Bedarf auf lokal Build umgestellt werden)
- Vanilla JS für interaktive Elemente (Chart.js, Debounce-Suche, Dark Mode Toggle)

**Trade-offs:**
- ✓ Einfaches Deployment, kein Node.js erforderlich
- ✓ SEO-freundlich (vollständiges HTML vom Server)
- ✗ Kein reaktives State-Management bei komplexen UI-Flows
- ✗ Keine Code-Splitting-Möglichkeiten

**Libraries:**
- `Chart.js 4.x` — Dashboard-Charts (CDN)
- `Alpine.js` — Lightweight reaktive Komponenten (optional, bei Bedarf)
- Tailwind CSS — Utility-First Styling

### Backend

**Choice:** FastAPI (Python 3.12) + Uvicorn

**Rationale:**
- Automatisches OpenAPI-Schema (NFR-012 ohne zusätzlichen Aufwand)
- Pydantic v2 für Request/Response-Validation (NFR-001: schnell durch Rust-Core)
- Async-Support für spätere Upgrades (ohne Framework-Wechsel)
- Python-Ökosystem für Prefect-Integration, SMTP, CSV-Parsing

**Trade-offs:**
- ✓ Auto-Docs, schnelle Entwicklung, Type-Safety
- ✗ GIL (Python) limitiert CPU-bound Concurrency — kein Problem für I/O-bound Web-App

**Key Libraries:**
- `SQLAlchemy 2.0` — ORM (sync Session für Einfachheit)
- `pydantic-settings` — Konfiguration aus `.env`
- `starlette SessionMiddleware` — Session-Cookies
- `bcrypt` — Passwort-Hashing (direkt, kein passlib — Python 3.14 inkompatibel)
- `aiosmtplib` — Async SMTP (für E-Mail-Service)
- `httpx` — Async HTTP-Client (für NocoDB/Prefect-API-Calls)
- `python-multipart` — File-Upload (CSV-Import)

### Database

**Choice:** SQLite mit WAL-Mode (→ PostgreSQL Migration Path)

**Rationale:**
- Zero-Setup, Volume-persistent in Docker
- WAL-Mode erlaubt multiple concurrent readers (NFR-011: 50 User)
- SQLAlchemy ORM abstrahiert Dialect-Unterschiede
- FTS5 (SQLite-native) → tsvector (PostgreSQL) isoliert in `search_service.py`

**Trade-offs:**
- ✓ Kein separater DB-Container, einfaches Backup (cp file)
- ✗ Kein horizontales Scaling der DB, kein Connection Pooling über Prozesse

**Migration Path:** `DATABASE_URL` env var wechseln + Alembic-Revision → fertig

### Infrastructure

**Choice:** Docker + Docker Compose → Coolify auf Proxmox LXC 110

**Rationale:**
- Coolify bietet Auto-Deploy, Health-Checks, Env-Var-Management ohne eigenes CI/CD-Infra
- LXC 110 hat Docker vorinstalliert, Port 8080 freigeschaltet
- Cloudflare Tunnel via LXC 104 (Caddy) für TLS-Terminierung ohne eigene Zertifikatsverwaltung

### Background Jobs

**Choice:** Prefect (LXC 109, automatisch.mitki.ai:4200)

**Rationale:**
- Bereits laufend, UI vorhanden, keine zusätzliche Infrastruktur nötig
- Retry-Logic, Scheduling, Observability out-of-the-box
- APScheduler hätte keinen UI, keine Retry-Sichtbarkeit

**Trade-offs:**
- ✓ Bessere Observability und Retry-Logic als in-process Scheduler
- ✗ Externe Abhängigkeit — Prefect-Ausfall stoppt Background Jobs

### Third-Party Services

| Service | Zweck | Implementierung |
|---------|-------|-----------------|
| Cloudflare | TLS + DNS | Tunnel via LXC 104 |
| SMTP (extern) | E-Mail-Versand | `aiosmtplib`, konfigurierbar via `.env` |
| NocoDB (LXC 106) | Icon-Bibliothek Admin-UI | REST API Abruf + lokaler Cache |
| Prefect (LXC 109) | Background Job Orchestration | HTTP-Trigger via `/api/v1/deployments/` |

---

## Part 4: System Components

### Component 1: API Layer (`app/api/`)

**Purpose:** HTTP-Eintrittspunkt für alle API-Clients und das Web-Frontend

**Responsibilities:**
- Request-Routing und HTTP-Methoden-Mapping
- Input-Validierung via Pydantic-Schemas
- Auth-Enforcement via `Depends(get_current_user)` und `Depends(require_role(...))`
- Response-Serialisierung und HTTP-Status-Codes
- OpenAPI-Dokumentation

**Interfaces:**
- REST: `GET/POST/PUT/DELETE /api/v1/{resource}`
- Health: `GET /health`, `GET /metrics`
- Docs: `GET /docs`, `GET /redoc`

**Dependencies:** Service Layer, Data Layer, `app/dependencies.py`

**FRs Addressed:** FR-001, FR-002, FR-003, FR-007, FR-008

---

### Component 2: Web Layer (`app/web/`)

**Purpose:** Server-Side-Rendered HTML-Seiten für Browser-Clients

**Responsibilities:**
- Jinja2-Template-Rendering mit Kontext-Daten
- Form-Handling (POST → Redirect-After-Post Pattern)
- Flash-Messages via Session
- Auth-Redirect für unauthentifizierte Requests

**Interfaces:**
- `GET/POST /login`, `/register`, `/logout`
- `GET /dashboard`
- `GET/POST /subscriptions`, `/subscriptions/{id}`, `/subscriptions/new`
- `GET /categories`, `/users`, `/audit-log`, etc.

**Dependencies:** Service Layer, `app/templates/`, `app/dependencies.py`

**FRs Addressed:** FR-006, FR-011, FR-012, FR-013, FR-020, FR-024

---

### Component 3: Service Layer (`app/services/`)

**Purpose:** Business Logic — kein HTTP, keine SQLAlchemy-Sessions als Parameter direkt

**Services:**

| Service | Verantwortlichkeit | FR |
|---------|-------------------|-----|
| `subscription_service.py` | Abo CRUD, Status-Berechnungen, Renewal-Logik | FR-004, FR-017 |
| `notification_service.py` | In-App Notifications erstellen/lesen | FR-016 |
| `email_service.py` | SMTP E-Mail-Versand via aiosmtplib | FR-010 |
| `search_service.py` | FTS5-Volltextsuche, Dialect-aware | FR-021, FR-035 |
| `audit_service.py` | Audit-Log-Einträge schreiben | FR-015 |
| `webhook_service.py` | Outgoing Webhooks, HMAC-Signatur, Retry | FR-026 |
| `icon_service.py` | Icon-Bibliothek, NocoDB-Abruf, Cache | FR-036, FR-037 |
| `analytics_service.py` | MRR, Churn, Revenue-Timeline | FR-014 |
| `import_export_service.py` | CSV/JSON Import/Export | FR-022 |

**Pattern:** Dependency Injection via FastAPI `Depends()`. Services erhalten `db: Session` als Parameter.

**FRs Addressed:** FR-004, FR-005, FR-010, FR-014, FR-015, FR-016, FR-017, FR-021, FR-022, FR-026, FR-036, FR-037

---

### Component 4: Data Layer (`app/models/`)

**Purpose:** ORM-Modelle und Datenbankzugriff

**Responsibilities:**
- SQLAlchemy 2.0 ORM-Modelle mit Typed Mapped Columns
- Relationship-Definitions
- Event-Listener für SQLite-Pragmas (WAL, Foreign Keys)
- Alembic-Migrations

**Pattern:** Repository-Pattern über Service Layer — kein direkter ORM-Zugriff in Routes

**FRs Addressed:** FR-001, FR-004, FR-005, FR-035

---

### Component 5: Background Jobs (`app/jobs/` + Prefect)

**Purpose:** Asynchrone, geplante Hintergrundaufgaben

**Prefect Flows (auf LXC 109):**

| Flow | Schedule | Aufgabe |
|------|----------|---------|
| `renewal_check_flow` | Täglich 08:00 | Abos mit `next_renewal <= today + notify_days` → E-Mail + Notification |
| `auto_renew_flow` | Täglich 08:05 | Auto-Renewal: `next_renewal` vorrücken |
| `expiry_check_flow` | Täglich 08:10 | Abgelaufene Abos → Status `expired` |
| `webhook_delivery_flow` | On-Demand | Webhook-Events mit Retry (3x Exponential Backoff) |

**Trigger:** FastAPI triggert Prefect via REST API bei Events (z.B. Abo-Erstellung löst `webhook_delivery_flow` aus)

**Lokal App (`app/jobs/`):** Nur leichte Tasks die keine Persistenz benötigen (z.B. Cache-Warmup)

**FRs Addressed:** FR-010, FR-016, FR-017, FR-026

---

### Component 6: Auth & Security (`app/core/`, `app/dependencies.py`)

**Purpose:** Authentifizierung, Autorisierung, Session-Management

**Responsibilities:**
- bcrypt Passwort-Hashing/-Verifikation
- Session-Cookie via `starlette.middleware.sessions.SessionMiddleware`
- `get_current_user()` → löst 401 aus wenn kein gültiger Session-Eintrag
- `get_current_tenant_id()` → liest `tenant_id` aus Session
- `require_role(["admin"])` → löst 403 aus bei falscher Rolle

**Upgrade Path zu JWT:** `get_current_user()` erkennt sowohl Cookie-Session als auch `Authorization: Bearer` Header

**FRs Addressed:** FR-002, FR-003, FR-031

---

### Component 7: Templates & Static (`app/templates/`, `static/`)

**Purpose:** UI-Layer mit Branding und Dark Mode

**Structure:**
```
app/templates/
├── base.html              # Layout + Navbar + Dark Mode + Flash Messages
├── components/            # Wiederverwendbare Partials (buttons, cards, modals)
├── pages/                 # Vollständige Seiten-Templates
└── emails/                # Jinja2 E-Mail-Templates (HTML + Text)

static/
├── js/
│   ├── charts.js          # Chart.js Dashboard-Integration
│   ├── search.js          # Debounced-Suche
│   └── notifications.js   # Polling (60s) für In-App Notifications
└── icons/                 # Lokaler Icon-Cache (aus NocoDB)
```

**FRs Addressed:** FR-011, FR-012, FR-020, FR-023, FR-033

---

## Part 5: Data Architecture

### Entity Relationship (vollständiges Schema)

```
tenants (id, name, slug, plan_tier, currency, locale, settings_json, is_active)
    │
    ├── users (id, tenant_id, email, password_hash, display_name, role,
    │          locale, is_active, last_login_at)
    │
    ├── subscriptions (id, tenant_id, plan_id, created_by_id, name, provider,
    │                  cost, currency, billing_cycle, status, start_date,
    │                  next_renewal, end_date, auto_renew, notify_days_before,
    │                  notes, custom_fields_json, icon_id)
    │          │
    │          └── subscription_categories (subscription_id, category_id)  [M2M]
    │
    ├── plans (id, tenant_id, name, description, price, currency,
    │         billing_cycle, features_json, is_active, sort_order)
    │
    ├── categories (id, tenant_id, name, color, icon)
    │
    ├── audit_log (id, tenant_id, user_id, action, entity_type, entity_id,
    │              old_values_json, new_values_json, ip_address, created_at)
    │              [append-only, keine UPDATE/DELETE erlaubt]
    │
    ├── notifications (id, tenant_id, user_id, title, message, type,
    │                  is_read, link, created_at)
    │
    ├── team_invitations (id, tenant_id, email, role, token, expires_at,
    │                     accepted_at, created_by_id)                        [NEU - FR-018]
    │
    ├── webhook_endpoints (id, tenant_id, url, events_json, secret,
    │                      is_active, created_at)                            [NEU - FR-026]
    │
    ├── webhook_deliveries (id, endpoint_id, event_type, payload_json,
    │                       response_status, attempts, last_attempt_at)      [NEU - FR-026]
    │
    ├── coupons (id, tenant_id, code, type, value, max_uses, use_count,
    │            valid_from, valid_until, is_active)                         [NEU - FR-027]
    │
    └── icon_cache (id, name, url, tags_json, category, etag,
                    synced_at)                                               [NEU - FR-036/037]

subscriptions_fts (VIRTUAL TABLE FTS5 - name, provider, notes)             [NEU - FR-021]
```

### Indexierungsstrategie

```sql
-- Tenant-scoped Queries (alle häufigen Abfragen)
CREATE INDEX idx_subscriptions_tenant ON subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_tenant_status ON subscriptions(tenant_id, status);
CREATE INDEX idx_subscriptions_next_renewal ON subscriptions(tenant_id, next_renewal);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read);
CREATE INDEX idx_audit_log_tenant ON audit_log(tenant_id, created_at DESC);
```

### Data Flow

**Read Path (Dashboard):**
```
Browser → GET /dashboard → pages.py → analytics_service.py
       → SQLAlchemy Query (indiziert, tenant_id Filter)
       → Jinja2 Template → HTML → Browser → Chart.js rendert
```

**Write Path (Abo erstellen):**
```
Browser → POST /subscriptions/new → pages.py → subscription_service.py
       → INSERT subscriptions → COMMIT
       → audit_service.py → INSERT audit_log
       → Prefect Trigger → webhook_delivery_flow (async)
       → Redirect → GET /subscriptions
```

**Background Path (tägliche Prüfung):**
```
Prefect Scheduler → renewal_check_flow
→ HTTP POST /api/v1/internal/renewal-check (signed with INTERNAL_API_KEY)
→ subscription_service.check_renewals()
→ email_service.send_renewal_reminder()
→ notification_service.create()
```

### PostgreSQL Migration

| SQLite | PostgreSQL Äquivalent | Aufwand |
|--------|----------------------|---------|
| `TEXT` (UUID) | `UUID` | Minimal (SQLAlchemy abstrahiert) |
| `TEXT` (JSON) | `JSONB` | `search_replace` in Modellen |
| FTS5 VIRTUAL TABLE | `tsvector` + GIN Index | `search_service.py` anpassen |
| `PRAGMA WAL` | nicht nötig | entfernen |

---

## Part 6: API Design

### API Architecture

- **Stil:** REST mit OpenAPI 3.0 (auto-generiert via FastAPI)
- **Versionierung:** URL-Prefix `/api/v1/`
- **Auth:** Cookie-Session (Web) + Bearer Token (API-Clients, ab FR-031)
- **Format:** JSON Request/Response
- **Pagination:** `?skip=0&limit=50` (Query-Params)
- **Fehler-Format:** `{"detail": "message"}` (FastAPI Standard)

### Complete API Endpoint Reference

#### Auth (`/api/v1/auth/`)
```
POST /api/v1/auth/register    - Tenant + Admin User erstellen
POST /api/v1/auth/login       - Session erstellen
POST /api/v1/auth/logout      - Session löschen
GET  /api/v1/auth/me          - Aktueller User
POST /api/v1/auth/token       - JWT ausstellen (FR-031)
POST /api/v1/auth/refresh     - JWT erneuern (FR-031)
```

#### Subscriptions (`/api/v1/subscriptions/`)
```
GET    /api/v1/subscriptions/           - Liste (filter: status, billing_cycle, category)
POST   /api/v1/subscriptions/           - Erstellen
GET    /api/v1/subscriptions/{id}       - Detail
PUT    /api/v1/subscriptions/{id}       - Aktualisieren
DELETE /api/v1/subscriptions/{id}       - Löschen
GET    /api/v1/subscriptions/export     - CSV/JSON Export (FR-022)
POST   /api/v1/subscriptions/import     - CSV/JSON Import (FR-022)
```

#### Plans (`/api/v1/plans/`)
```
GET    /api/v1/plans/           - Liste
POST   /api/v1/plans/           - Erstellen (Admin only)
PUT    /api/v1/plans/{id}       - Aktualisieren (Admin only)
DELETE /api/v1/plans/{id}       - Löschen (Admin only)
```

#### Categories (`/api/v1/categories/`)
```
GET    /api/v1/categories/      - Liste
POST   /api/v1/categories/      - Erstellen
PUT    /api/v1/categories/{id}  - Aktualisieren
DELETE /api/v1/categories/{id}  - Löschen
```

#### Users (`/api/v1/users/`)
```
GET    /api/v1/users/           - Team-Mitglieder (Admin only)
POST   /api/v1/users/invite     - Einladung senden (FR-018)
PUT    /api/v1/users/{id}       - Rolle ändern (Admin only)
DELETE /api/v1/users/{id}       - Deaktivieren (Admin only)
```

#### Notifications (`/api/v1/notifications/`)
```
GET  /api/v1/notifications/           - Liste (unread first)
POST /api/v1/notifications/{id}/read  - Als gelesen markieren
POST /api/v1/notifications/read-all   - Alle als gelesen markieren
```

#### Search (`/api/v1/search/`)
```
GET /api/v1/search/?q={query}   - FTS5 Volltextsuche (FR-021)
```

#### Analytics (`/api/v1/analytics/`)
```
GET /api/v1/analytics/dashboard  - KPIs, MRR, Churn (Admin only, FR-014)
GET /api/v1/analytics/revenue    - Revenue Timeline 12 Monate
```

#### Webhooks (`/api/v1/webhooks/`)
```
GET    /api/v1/webhooks/         - Registrierte Endpoints (FR-026)
POST   /api/v1/webhooks/         - Endpoint registrieren
DELETE /api/v1/webhooks/{id}     - Endpoint löschen
POST   /api/v1/webhooks/{id}/test - Test-Event senden
```

#### Coupons (`/api/v1/coupons/`)
```
GET    /api/v1/coupons/          - Liste (Admin only, FR-027)
POST   /api/v1/coupons/          - Erstellen
PUT    /api/v1/coupons/{id}      - Aktualisieren
POST   /api/v1/coupons/validate  - Code prüfen
```

#### Icons (`/api/v1/icons/`)
```
GET /api/v1/icons/               - Icon-Bibliothek (mit Cache, FR-036)
GET /api/v1/icons/?q={query}     - Icons suchen nach Name/Tag
POST /api/v1/icons/sync          - Cache aus NocoDB aktualisieren (Admin only)
```

#### Monitoring
```
GET /health   - Systemstatus + DB-Check (FR-008)
GET /metrics  - Tenant/User/Abo-Counts (FR-008)
```

### Internal API (Prefect → App)

```
POST /api/v1/internal/renewal-check   - Prefect-Flow triggert tägliche Prüfung
POST /api/v1/internal/webhook-deliver - Prefect-Flow liefert Webhook aus
```
Geschützt durch `X-Internal-Key: {INTERNAL_API_KEY}` Header (aus `.env`)

---

## Part 7: NFR Coverage

### NFR-001: API Response Time (< 500ms p95)

**Architektur-Lösung:**
- SQLite WAL-Mode: keine Read-Locks
- Alle listen-Queries indiziert (idx auf `tenant_id`, composite indexes)
- Pydantic v2 (Rust-Core): schnelle Serialisierung
- Jinja2 Template-Caching (Produktions-Modus)
- Kein N+1: `selectinload()` für Relationships statt lazy loading

**Implementation:** `db.query(Subscription).options(selectinload(Subscription.categories)).filter(...)` überall wo Relationships benötigt

**Validation:** `pytest` + `httpx` Load-Test mit `locust` nach Phase 1

---

### NFR-002: Dashboard Load Time (< 2s)

**Architektur-Lösung:**
- Dashboard-KPIs in einem SQL-Aggregate-Query berechnet (kein N+1)
- Chart.js lazy-loaded (async script tag)
- Tailwind CDN → bei Bedarf lokaler Build (dann ~10KB statt ~300KB)
- Analytics-Daten im Service Layer gecached (60s in-memory, `functools.lru_cache` mit TTL)

**Implementation:** `analytics_service.get_dashboard_kpis(tenant_id)` gibt alle Zahlen in einem DB-Round-Trip zurück

---

### NFR-003: Uptime 99%

**Architektur-Lösung:**
- Docker `restart: unless-stopped`
- Coolify Health-Check: `GET /health` alle 30s, Restart bei Fehler
- SQLite WAL verhindert korrupte DB bei unclean Shutdown
- Coolify Auto-Restart + Alerting

**Validation:** Coolify Dashboard zeigt Uptime-Statistiken

---

### NFR-004: Password Storage (bcrypt rounds=12)

**Architektur-Lösung:**
- `app/core/security.py`: direkte bcrypt-Nutzung (kein passlib — Python 3.14 inkompatibel)
- `hash_password()` und `verify_password()` als einzige Einstiegspunkte

**Implementation:** Bereits implementiert und getestet

---

### NFR-005: Session Security

**Architektur-Lösung:**
- Starlette `SessionMiddleware` mit `secret_key` aus `settings.app_secret_key`
- Cookie: `HttpOnly=True`, `SameSite=lax`
- `Secure=True` in Production (gesetzt via Middleware + Env-Var)
- Session-Inhalt ist HMAC-signiert (Starlette Standard)

**Implementation:** `app/main.py: app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key, https_only=settings.is_production)`

---

### NFR-006: Tenant Data Isolation

**Architektur-Lösung:**
- `get_current_tenant_id()` Dependency — liest aus Session, niemals aus Request-Body
- Alle Service-Methoden nehmen `tenant_id: str` als ersten Parameter
- Alle DB-Queries enthalten `.filter(Model.tenant_id == tenant_id)`
- Keine globalen Queries ohne tenant_id (außer interne Admin-Endpoints)
- Automatisierte Isolation-Tests in `tests/test_tenant_isolation.py`

**Validation:** `tests/test_tenant_isolation.py` — User A kann User B's Subscriptions nicht sehen/ändern

---

### NFR-007: Browser Support (last 2 versions)

**Architektur-Lösung:**
- Kein experimenteller JS-API-Einsatz
- Tailwind CSS: vollständige Browser-Kompatibilität
- `localStorage` für Dark Mode (breit unterstützt)
- Kein ES2022+ Features ohne Polyfill (vanilla JS im `<script>` bleibt ES2015+)

---

### NFR-008: Mobile Breakpoints

**Architektur-Lösung:**
- Tailwind Breakpoints: `sm:` (640px), `md:` (768px), `lg:` (1024px), `xl:` (1440px)
- Sidebar: `hidden lg:block` (Desktop) / Hamburger auf Mobile
- Tabellen: `overflow-x-auto` Container
- Buttons: `min-h-[44px] min-w-[44px]` überall

---

### NFR-009: Test Coverage ≥ 70%

**Architektur-Lösung:**
```
tests/
├── test_auth.py              # Login, Register, Logout, Sessions
├── test_subscriptions.py     # CRUD + Filterung
├── test_plans.py             # CRUD
├── test_tenant_isolation.py  # Cross-tenant access denied
├── test_notifications.py     # Create, Read, Mark-read
├── test_search.py            # FTS5 Queries
├── test_analytics.py         # MRR, Churn Berechnungen
├── test_webhooks.py          # HMAC, Delivery
└── conftest.py               # TestClient, DB-Fixtures, Tenant-Fixtures
```

**Pattern:**
- `conftest.py` erstellt In-Memory SQLite DB für jeden Test
- `TestClient` aus `fastapi.testclient`
- Kritische Pfade (Auth, Isolation): 90%+ Coverage Ziel

---

### NFR-010: Code Quality (ruff + mypy)

**Architektur-Lösung:**
```yaml
# .github/workflows/ci.yml
- name: Lint
  run: ruff check app/ tests/
- name: Type Check
  run: mypy app/ --ignore-missing-imports
- name: Tests
  run: pytest --cov=app --cov-report=term-missing --cov-fail-under=70
```

**Pre-commit:** `ruff` + `mypy` als pre-commit Hooks für lokale Entwicklung

---

### NFR-011: 50 Concurrent Users

**Architektur-Lösung:**
- SQLite WAL-Mode: concurrent Reads ohne Locks
- Uvicorn: Multi-Worker via `--workers 2` (Gunicorn als Process Manager optional)
- Connection Pool: `StaticPool` für Tests, `QueuePool` für Production
- Async-Support: FastAPI + Uvicorn sind ASGI, I/O wird non-blocking behandelt

**Skalierungs-Pfad:** Bei > 200 concurrent Users → PostgreSQL + Connection Pooling

---

### NFR-012: OpenAPI 3.0

**Architektur-Lösung:**
- FastAPI generiert OpenAPI 3.0 Schema automatisch
- Pydantic Response Models = präzise Schema-Definitionen
- `/docs` (Swagger UI), `/redoc` (ReDoc), `/openapi.json`

**Implementation:** Bereits aktiv, kein zusätzlicher Aufwand

---

## Part 8: Security Architecture

### Authentication

**Current (Phase 1-3):**
```
POST /api/v1/auth/login
→ verify_password(plain, hash) via bcrypt
→ request.session["user_id"] = user.id
→ Starlette SessionMiddleware (HMAC-signed cookie)
→ Cookie: HttpOnly, SameSite=Lax, Secure (Production)
```

**Upgrade (Phase 4, FR-031):**
```
POST /api/v1/auth/token
→ Returns: {"access_token": JWT, "refresh_token": JWT}
→ Access: 15 min, Refresh: 7 Tage
→ Web: Cookie bleibt Session-basiert (enthält JWT intern)
→ API: Bearer Token in Authorization Header
→ get_current_user() unterstützt beide Methoden
```

### Authorization

**RBAC Matrix:**

| Action | admin | user | viewer |
|--------|-------|------|--------|
| Dashboard lesen | ✓ | ✓ | ✓ |
| Subscription CRUD | ✓ | ✓ | - |
| Plan CRUD | ✓ | - | - |
| User einladen | ✓ | - | - |
| Audit Log | ✓ | - | - |
| Analytics | ✓ | - | - |
| Webhook-Endpoints | ✓ | - | - |

**Enforcement:** `require_role(["admin"])` Dependency in FastAPI-Routen

### Encryption

**At Rest:**
- Passwörter: bcrypt (irreversibel)
- Session: HMAC-signiert (Starlette)
- SQLite-Datei: Unverschlüsselt auf Host — Proxmox-LXC-Ebene (Storage-Encryption optional)

**In Transit:**
- Cloudflare → Caddy: HTTPS (TLS terminiert bei Cloudflare)
- Caddy → LXC 110: HTTP intern (private Netzwerk, akzeptabel für interne Proxmox-Kommunikation)
- `header_up X-Forwarded-Proto https` in Caddy (Starlette erkennt HTTPS korrekt)

### Input Validation

- Alle API-Inputs via Pydantic-Schemas validiert (Type, Required, Max-Length)
- HTML-Forms: CSRF-Schutz via SameSite=Lax Cookie + session-basiertes Formular-Token
- SQL-Injection: SQLAlchemy ORM verhindert durch parameterisierte Queries
- XSS: Jinja2 auto-escaping (standardmäßig aktiv)

### Security Headers (via Caddy)

```
header {
    Strict-Transport-Security "max-age=31536000"
    X-Content-Type-Options "nosniff"
    X-Frame-Options "DENY"
    Referrer-Policy "strict-origin-when-cross-origin"
}
```

---

## Part 9: Scalability & Performance

### Scaling Strategy

**Jetzt (Phase 1-3):** Single Docker Container + SQLite
- Ausreichend für 50 concurrent User (NFR-011)
- SQLite WAL: multiple readers, single writer

**Phase 4-5:** PostgreSQL Migration
```
1. Alembic-Revision mit dialect-aware Migration
2. DATABASE_URL in Coolify-Config ändern
3. `search_service.py`: FTS5 → tsvector
4. `app/database.py`: WAL Pragma entfernen, Connection Pooling aktivieren
```

**Langfristig (nach Launch):**
- Coolify: Load-Balancer + 2 App-Instanzen
- PostgreSQL Read-Replicas für Analytics-Queries
- Redis für Session-Storage (statt Cookie) und Icon-Cache

### Performance-Optimierungen (konkret)

1. **Kein N+1**: Überall `selectinload()` für Relationships
2. **Aggregate-Queries**: Dashboard-KPIs in einer SQL-Query
3. **Pagination**: Max 100 Items pro Request
4. **Debounce**: Suche mit 300ms Debounce (FR-021)
5. **Chart.js async**: `<script async src="...">` — blockiert kein Rendering
6. **Icon-Cache**: In-Memory TTL 60min (NocoDB wird nicht bei jedem Request abgefragt)

---

## Part 10: Reliability & Availability

### High Availability (Single-Node)

```
Docker Container (LXC 110)
├── restart: unless-stopped
├── HEALTHCHECK CMD curl /health
└── Coolify: Auto-Restart bei Failed Health-Check
```

**Single Point of Failure:** LXC 110 / Proxmox Host
**Mitigation:** Proxmox-Backup auf Synology NAS (täglich)

### Disaster Recovery

| Was | RPO | RTO | Lösung |
|-----|-----|-----|--------|
| SQLite DB | 24h | < 1h | Täglicher Proxmox-Backup der LXC |
| App-Code | 0 | < 15min | GitHub + Coolify Auto-Deploy |
| Environment-Vars | - | < 15min | In Coolify gespeichert |

**Backup-Prozess:**
```bash
# Manuelles DB-Backup (bei SQLite WAL sicher)
sqlite3 /data/subscriptions.db ".backup '/data/backup-$(date +%Y%m%d).db'"
```

### Monitoring & Alerting

| Layer | Tool | Was |
|-------|------|-----|
| App | `/health` + Coolify | Uptime, Container-Status |
| Metrics | `/metrics` + Grafana | Abo-Counts, User-Counts |
| Logs | Docker logs → Loki (FR-032) | Errors, Request-IDs |
| Alerts | Coolify Webhooks → n8n (LXC 102) | Health-Check Failures |

**Logging-Format (FR-032):**
```python
import structlog
log = structlog.get_logger()
log.info("subscription.created", tenant_id=..., sub_id=..., request_id=...)
```

---

## Part 11: Development & Deployment

### Project Structure (vollständig)

```
subscription-manager/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── api/
│   │   ├── health.py
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── subscriptions.py
│   │       ├── plans.py
│   │       ├── categories.py        [TODO]
│   │       ├── users.py             [TODO]
│   │       ├── notifications.py     [TODO]
│   │       ├── search.py            [TODO]
│   │       ├── analytics.py         [TODO]
│   │       ├── webhooks.py          [TODO]
│   │       ├── coupons.py           [TODO]
│   │       └── icons.py             [TODO]
│   ├── core/
│   │   ├── security.py
│   │   └── middleware.py            [TODO: request_id, structured logging]
│   ├── models/
│   │   ├── tenant.py, user.py, subscription.py
│   │   ├── plan.py, category.py, audit.py, notification.py
│   │   ├── team_invitation.py       [TODO]
│   │   ├── webhook.py               [TODO]
│   │   ├── coupon.py                [TODO]
│   │   └── icon_cache.py            [TODO]
│   ├── schemas/                     # Pydantic Request/Response
│   ├── services/                    # Business Logic [ALLE TODO außer was in Routes]
│   ├── jobs/                        # Prefect Flow Trigger [TODO]
│   ├── web/routes/pages.py          [ERWEITERN]
│   └── templates/                   # Jinja2 [ERWEITERN]
├── static/js/
├── translations/de.json, en.json    [TODO]
├── migrations/                      [TODO: Alembic]
├── tests/
├── scripts/seed.py
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── docker-compose.staging.yml       [TODO]
└── pyproject.toml                   [TODO: ruff, mypy config]
```

### CI/CD Pipeline

```
Feature-Branch → PR → GitHub Actions:
    1. ruff check app/ tests/          (NFR-010)
    2. mypy app/                       (NFR-010)
    3. pytest --cov=app --cov-fail-under=70  (NFR-009)
    4. docker build (smoke test)
    ↓ (nur bei staging/main)
staging Branch → Coolify "SubManager-Staging" (Port 8081)
    ↓ PR Review
main Branch → Coolify "SubManager-Production" (Port 8080)
```

### Deployment-Konfiguration

```yaml
# Coolify App: SubManager-Production
Branch: main
Port: 8080 → 8000
Health Check: GET /health
Volume: /data (persistent SQLite)
Env:
  APP_SECRET_KEY=<random-64-chars>
  DATABASE_URL=sqlite:////data/subscriptions.db
  SMTP_HOST=...
  INTERNAL_API_KEY=<random-32-chars>
  IS_PRODUCTION=true
```

### Testing Strategy

```
Unit Tests:     Service Layer (pure functions)           → 90%+ Coverage
Integration:    API Layer mit TestClient + In-Memory DB   → alle Endpoints
Isolation:      Cross-Tenant Zugriff verweigert          → 100% Coverage
E2E:            Optional: Playwright für kritische Flows
Performance:    Locust Load-Test (50 concurrent users)
```

---

## Part 12: FR Traceability Matrix

| FR ID | Titel | Komponente | Sprint |
|-------|-------|-----------|--------|
| FR-001 | Multi-Tenant Isolation | Data Layer + Dependencies | ✅ Done |
| FR-002 | User Authentication | Auth API + Security | ✅ Done |
| FR-003 | RBAC | Dependencies + require_role() | ✅ Done |
| FR-004 | Subscription CRUD | API v1 + Service + Model | ✅ Done |
| FR-005 | Plan Management | API v1 + Service + Model | ✅ Done |
| FR-006 | Web Dashboard | Web Routes + Templates + Chart.js | Sprint 2 |
| FR-007 | Public REST API | API v1 (Router, Swagger) | ✅ Done |
| FR-008 | Health/Metrics | health.py | Sprint 2 |
| FR-009 | Docker Deployment | Dockerfile + docker-compose.yml | ✅ Done |
| FR-010 | E-Mail Notifications | email_service.py + Prefect Flow | Sprint 3 |
| FR-011 | Branding | base.html + Tailwind Config | ✅ Done |
| FR-012 | Responsive Design | Templates + Tailwind Breakpoints | Sprint 2 |
| FR-013 | Self-Service Portal | Web Routes + subscription_service | Sprint 4 |
| FR-014 | Admin Analytics | analytics_service.py + API | Sprint 6 |
| FR-015 | Audit Log | audit_service.py + Model | Sprint 3 |
| FR-016 | In-App Notifications | notification_service.py + Polling-JS | Sprint 3 |
| FR-017 | Workflow Automation | Prefect Flows | Sprint 3 |
| FR-018 | Teams/Organisationen | users.py API + team_invitation Model | Sprint 4 |
| FR-019 | Tags/Kategorien | categories.py API + M2M | Sprint 2 |
| FR-020 | Dark Mode | base.html JS + localStorage | Sprint 2 |
| FR-021 | Volltextsuche | search_service.py + FTS5 | Sprint 5 |
| FR-022 | Import/Export | import_export_service.py | Sprint 5 |
| FR-023 | Internationalisierung | translations/ + i18n Middleware | Sprint 5 |
| FR-024 | Onboarding Wizard | Web Routes + Session-Flag | Sprint 4 |
| FR-025 | Multi-Currency | Subscription Model (existing) + UI | Sprint 2 |
| FR-026 | Outgoing Webhooks | webhook_service.py + Prefect | Sprint 6 |
| FR-027 | Coupons | coupon.py API + Model | Sprint 6 |
| FR-028 | SSO (Google/MS) | auth.py + OAuth2 Libraries | Sprint 8 |
| FR-029 | GraphQL API | strawberry_graphql + /graphql route | Sprint 9 |
| FR-030 | Custom Fields | custom_fields_json (existing) + UI | Sprint 6 |
| FR-031 | OAuth2/JWT Upgrade | auth.py + JWT Middleware | Sprint 8 |
| FR-032 | Structured Logging | core/middleware.py + structlog | Sprint 7 |
| FR-033 | YouTube Showcase | Landing Page + seed.py Erweiterung | Sprint 10 |
| FR-034 | Staging Environment | docker-compose.staging.yml + Coolify | Sprint 1 |
| FR-035 | DB Migration Path | search_service.py + Alembic | Sprint 5 |
| FR-036 | Icon Bibliothek | icon_service.py + icon_cache Model | Sprint 5 |
| FR-037 | NocoDB Integration | icon_service.py (NocoDB Client) | Sprint 6 |

### NFR Traceability Matrix

| NFR ID | Titel | Lösung | Validation |
|--------|-------|--------|------------|
| NFR-001 | API < 500ms p95 | Indexes + selectinload + Pydantic v2 | Locust Load Test |
| NFR-002 | Dashboard < 2s | Aggregate Query + Chart.js async | Browser DevTools |
| NFR-003 | 99% Uptime | Docker restart + Coolify Health Check | Coolify Dashboard |
| NFR-004 | bcrypt rounds=12 | security.py direkt | Unit Test |
| NFR-005 | Session Security | SessionMiddleware + HttpOnly | Browser Inspector |
| NFR-006 | Tenant Isolation | tenant_id in allen Queries | test_tenant_isolation.py |
| NFR-007 | Browser Support | Vanilla JS + Tailwind | Manual Test |
| NFR-008 | Mobile 320px+ | Tailwind Breakpoints | Browser DevTools |
| NFR-009 | 70% Coverage | pytest --cov | CI Report |
| NFR-010 | ruff + mypy | CI Pipeline | CI Block on Error |
| NFR-011 | 50 concurrent | SQLite WAL + Uvicorn | Locust |
| NFR-012 | OpenAPI 3.0 | FastAPI auto-gen | /openapi.json |

---

## Part 13: Major Trade-offs

### Trade-off 1: Monolith vs. Microservices
**Entscheidung:** Layered Modular Monolith
**Gewinn:** Einfaches Deployment, kein Distributed-Systems-Overhead, schnelle Entwicklung
**Verlust:** Kein unabhängiges Skalieren einzelner Services
**Rationale:** Level 3 Projekt mit einem Entwickler — Microservices wären premature complexity

### Trade-off 2: SQLite vs. PostgreSQL
**Entscheidung:** SQLite mit explizitem Migration Path
**Gewinn:** Zero-Setup, einfaches Backup, kein DB-Container
**Verlust:** Kein Connection Pooling über Prozesse, kein horizontales DB-Scaling
**Rationale:** Für MVP und Early Adopters (< 200 concurrent User) ausreichend

### Trade-off 3: SSR vs. SPA
**Entscheidung:** Jinja2 SSR + Vanilla JS
**Gewinn:** Kein Build-Step, SEO-freundlich, sofort deploybar
**Verlust:** Kein reaktives State-Management für komplexe UI-Flows
**Rationale:** Zeit-to-Market wichtiger als UI-Raffinesse in Phase 1-3

### Trade-off 4: In-Process Scheduler vs. Prefect
**Entscheidung:** Prefect (extern, LXC 109)
**Gewinn:** UI, Retry-Logic, Observability ohne eigenen Code
**Verlust:** Externe Abhängigkeit — Prefect-Ausfall stoppt Background Jobs
**Rationale:** Prefect läuft bereits, keine zusätzliche Infrastruktur nötig

### Trade-off 5: Session Cookies vs. JWT
**Entscheidung:** Session Cookies (Phase 1-3), JWT-Upgrade (Phase 4)
**Gewinn (Phase 1):** Einfache Implementierung, kein Token-Rotation-Overhead
**Verlust:** Kein stateless Auth (Server muss Session kennen)
**Rationale:** Upgrade-Pfad eingebaut (`get_current_user()` wird dual-mode)

---

## Validation Checklist

- [x] Alle 37 FRs haben Component-Zuweisungen (FR Traceability Matrix)
- [x] Alle 12 NFRs haben architekturelle Lösungen (Part 7)
- [x] Technology Choices sind begründet (Part 3)
- [x] Trade-offs sind dokumentiert (Part 13)
- [x] Security ist umfassend adressiert (Part 8)
- [x] Skalierungspfad ist klar (Part 9)
- [x] Datenmodell ist vollständig definiert (Part 5)
- [x] API-Kontrakte sind spezifiziert (Part 6)
- [x] Testing-Strategie ist definiert (Part 11)
- [x] Deployment-Ansatz ist beschrieben (Part 11)

---

## Next Steps

### Sofort (Sprint 1 Abschluss)
1. `docker-compose.staging.yml` erstellen (FR-034)
2. `pyproject.toml` mit ruff + mypy Config
3. `.github/workflows/ci.yml` vervollständigen

### Sprint 2
1. Dashboard mit Chart.js Charts (FR-006)
2. Categories API + M2M UI (FR-019)
3. Dark Mode vollständig (FR-020)
4. `/metrics` Endpoint (FR-008)

### Sprint 3
1. `services/` Layer einführen (Refactor aus Routes)
2. `audit_service.py` + Audit-Log-Seite (FR-015)
3. `notification_service.py` + Polling JS (FR-016)
4. Prefect Flows für E-Mail + Auto-Renewal (FR-010, FR-017)

**Next BMAD Step:** `/bmad:sprint-planning` — Epic in Stories aufteilen und Sprint 2 planen
