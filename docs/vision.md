---
name: Vision Subscription Manager
description: Alle 50 J/N Entscheidungen für den Subscription Manager SaaS inkl. Tech-Stack
type: project
---

## Tech-Stack (festgelegt)
- Backend: FastAPI (Python) + Uvicorn
- ORM: SQLAlchemy 2.0 + SQLite (→ PostgreSQL Migrationspfad)
- Validation: Pydantic-Settings
- Scheduler: APScheduler
- Auth: HTTP Basic Auth (→ OAuth2/JWT + SSO)
- Frontend: Jinja2 SSR + Tailwind CSS (CDN) + Vanilla JS
- Container: Docker + Docker Compose (8080→8000)
- Deployment: Coolify auf Proxmox
- Git: GitHub

## JA-Features (36)
SaaS-Produkt, Web-Dashboard, mitKI.ai Branding, Abo-Pläne (Basic/Pro/Enterprise), RBAC, E-Mail-Notifications, Public REST API, Multi-Tenant, Self-Service Portal, DB-Migrationspfad, OAuth2/JWT-Pfad, Admin Analytics Dashboard, Coolify Auto-Deploy, GitHub, Webhooks, Import/Export (CSV/JSON), i18n (DE+EN), Audit Log, pytest+CI, Volltextsuche, Dark Mode, Workflow-Automation, In-App Notifications, Health/Metrics Endpoints, Onboarding Wizard, Tags/Kategorien, Teams/Organisationen, Responsive, Staging+Prod, Loki/Grafana Logging, Multi-Currency, Coupons/Rabattcodes, SSO (Google/Microsoft), GraphQL+REST, Custom Fields, YouTube Showcase

## NEIN-Features (14)
Kein Payment-Processing, kein Rate-Limiting, kein DB-Backup, keine Kalender-Integration, kein Activity-Feed, keine Status-Page, kein PDF-Export, kein Plugin-System, kein Trial, keine API-Key-Verwaltung, keine DSGVO-Features

**Why:** Showcase-Projekt für mitKI.ai YouTube-Kanal + echtes SaaS-Produkt
**How to apply:** MVP-first Ansatz, Feature-Scope bei Implementierung beachten
