# Sprint Plan: Subscription Manager

**Date:** 2026-03-29
**Scrum Master:** Eddy (mitKI.ai)
**Developer:** Claude (AI)
**Project Level:** 3 (Multi-Tenant SaaS)
**Total Stories:** 46 (9 done + 37 planned)
**Total Points:** 215 (37 done + 178 planned)
**Planned Sprints:** 9 (Sprint 1 abgeschlossen)

---

## Kapazitätsmodell

**Developer:** Claude (AI-Session-basiert)
**Sprint-Kapazität:** 15–25 Story Points pro Session
**Sprint-Länge:** Eine Claude-Coding-Session
**Done-Kriterium:** `pytest` grün für alle neuen Acceptance Criteria

**TDD-Workflow (spec-driven):**
```
1. Acceptance Criteria aus Story → Pytest-Test-Cases definieren
2. Tests schreiben (fail expected)
3. Implementierung bis Tests grün
4. Refactor + Linting (ruff check)
5. Sprint Done ✅
```

**Sizing-Kalibrierung für Claude:**
| Punkte | Aufwand | Beispiel |
|--------|---------|---------|
| 1 | Trivial | Config-Wert, Text-Änderung |
| 2 | Einfach | Einzelner Endpoint oder Template-Partial |
| 3 | Moderat | Feature mit Tests (~45-60 Min) |
| 5 | Komplex | Feature mit mehreren Komponenten + Tests |
| 8 | Sehr komplex | Vollständiger User-Flow (Frontend + Backend + Tests) |

---

## Executive Summary

Sprint 1 ist abgeschlossen und liefert die MVP-Basis: Auth, CRUD, Docker-Deployment, Health-Endpoints, mitKI.ai-Branding. Sprints 2–9 bauen darauf auf und liefern in jeder Session sofort testbare Features — von Dashboard-Charts bis SSO-Login.

**Alle Sprints liefern deploybare, getestete Software.** Kein Sprint endet ohne grüne Tests.

---

## Story Inventory

### ✅ SPRINT 1 — ABGESCHLOSSEN (Baseline MVP)

---

#### STORY-001: Multi-Tenant Data Isolation ✅
**Epic:** EPIC-001 | **Priority:** Must Have | **Points:** 5

**User Story:**
Als Tenant-Admin möchte ich, dass meine Daten vollständig von anderen Tenants getrennt sind, damit kein Datenleck möglich ist.

**Acceptance Criteria:**
- [x] Jeder API-Call filtert automatisch nach `tenant_id`
- [x] User A kann User B's Subscriptions nicht abrufen (HTTP 200 mit leerer Liste oder 404)
- [x] `get_current_tenant_id()` Dependency in jeder Route aktiv

**Tests:** `tests/test_tenant_isolation.py`

---

#### STORY-002: User Authentication (Login/Register/Logout) ✅
**Epic:** EPIC-001 | **Priority:** Must Have | **Points:** 5

**User Story:**
Als Benutzer möchte ich mich mit E-Mail und Passwort anmelden können, damit ich auf meine Daten zugreifen kann.

**Acceptance Criteria:**
- [x] Login mit E-Mail + Passwort funktioniert
- [x] Passwörter werden mit bcrypt (rounds=12) gehasht
- [x] Logout löscht Session vollständig
- [x] Fehlgeschlagene Logins: generische Fehlermeldung

**Tests:** `tests/test_auth.py`

---

#### STORY-003: Rollenbasierte Zugriffskontrolle (RBAC) ✅
**Epic:** EPIC-001 | **Priority:** Must Have | **Points:** 3

**User Story:**
Als Admin möchte ich Rollen (admin/user/viewer) vergeben können, damit Zugriffe korrekt eingeschränkt werden.

**Acceptance Criteria:**
- [x] `require_role(["admin"])` gibt HTTP 403 für non-admins
- [x] Viewer-Rolle kann keine Mutations ausführen
- [x] Rolle wird aus DB geladen, nicht aus Session

**Tests:** `tests/test_auth.py::test_rbac_*`

---

#### STORY-004: Subscription CRUD (API + Web) ✅
**Epic:** EPIC-002 | **Priority:** Must Have | **Points:** 8

**User Story:**
Als Benutzer möchte ich Abonnements erstellen, bearbeiten und löschen können.

**Acceptance Criteria:**
- [x] POST /api/v1/subscriptions/ erstellt Abo
- [x] PUT /api/v1/subscriptions/{id} aktualisiert Abo
- [x] DELETE /api/v1/subscriptions/{id} löscht Abo
- [x] GET /api/v1/subscriptions/ mit skip/limit Pagination
- [x] Filter nach Status und Billing-Cycle
- [x] Web-Formulare für Create/Edit
- [ ] Filter nach Kategorie (→ STORY-012)

**Tests:** `tests/test_subscriptions.py`

---

#### STORY-005: Plan Management ✅
**Epic:** EPIC-002 | **Priority:** Must Have | **Points:** 5

**User Story:**
Als Admin möchte ich Abo-Plan-Vorlagen verwalten, damit Benutzer daraus wählen können.

**Acceptance Criteria:**
- [x] CRUD für Plans (Admin-only)
- [x] `plan_id` FK in Subscription nutzbar
- [x] `features_json` speicherbar
- [x] Sortierung per `sort_order`

**Tests:** `tests/test_plans.py`

---

#### STORY-006: Public REST API + Swagger ✅
**Epic:** EPIC-006 | **Priority:** Must Have | **Points:** 3

**Acceptance Criteria:**
- [x] `/docs` Swagger UI erreichbar
- [x] `/redoc` erreichbar
- [x] `/openapi.json` valides Schema
- [x] API-Prefix `/api/v1/`

---

#### STORY-007: Health + Metrics Endpoints ✅
**Epic:** EPIC-001 | **Priority:** Must Have | **Points:** 2

**Acceptance Criteria:**
- [x] `GET /health` → `{"status": "ok", "version": ..., "database": "ok"}`
- [x] `GET /metrics` → tenant/user/subscription counts
- [x] Kein Auth erforderlich
- [x] Response < 100ms

---

#### STORY-008: Docker + Docker Compose Deployment ✅
**Epic:** EPIC-001 | **Priority:** Must Have | **Points:** 3

**Acceptance Criteria:**
- [x] `docker compose up` startet erfolgreich
- [x] SQLite-Volume `/data` persistiert
- [x] Health-Check im Dockerfile
- [x] `.env` konfigurierbar
- [ ] Image < 500MB (→ STORY-016)

---

#### STORY-009: mitKI.ai Branding Base ✅
**Epic:** EPIC-002 | **Priority:** Must Have | **Points:** 3

**Acceptance Criteria:**
- [x] CSS Custom Properties `--navy`, `--orange`, `--creme`
- [x] Tailwind mit Brand-Colors
- [x] Inter + Montserrat Fonts geladen
- [x] Konsistentes Layout über alle Seiten
- [ ] Logo SVG/PNG (→ STORY-016)

---

**Sprint 1 Total: 37 Points ✅**

---

### 🔜 SPRINT 2 — Dashboard + Kategorien + Responsive (27 Points)

**Sprint-Ziel:** Das Dashboard wird zu einem vollwertigen KPI-Center mit Charts. Kategorien-System ist vollständig und filterbar. App ist mobile-ready.

**Liefert:** Vollständig nutzbares Dashboard, Kategorie-Management, responsive UI auf allen Breakpoints.

---

#### STORY-010: Dashboard Charts + 30-Tage Renewals
**Epic:** EPIC-002 | **Priority:** Must Have | **Points:** 5

**User Story:**
Als Benutzer möchte ich auf dem Dashboard Charts sehen, damit ich meine Kosten auf einen Blick verstehe.

**Acceptance Criteria:**
- [ ] Summary-Card: Monatliche Gesamtkosten (korrekt normalisiert)
- [ ] Summary-Card: Anstehende Verlängerungen 7 Tage UND 30 Tage
- [ ] Balkendiagramm: Kosten nach Billing-Cycle (Chart.js)
- [ ] Donut-Chart: Kosten-Breakdown nach Kategorie (Chart.js)
- [ ] Dashboard lädt vollständig in < 2s (lokal gemessen)

**Technical Notes:**
- Chart.js via CDN (`<script async>`)
- Dashboard-KPIs in einem Aggregate-Query (kein N+1)
- `app/web/routes/pages.py::dashboard()` erweitern
- Chart-Daten als JSON in Jinja2-Template inline

**Tests:** `tests/test_web.py::test_dashboard_stats_*`

**Dependencies:** STORY-004 (done)

---

#### STORY-011: Kategorien CRUD API + Web UI
**Epic:** EPIC-002 | **Priority:** Should Have | **Points:** 5

**User Story:**
Als Admin möchte ich Kategorien mit Farbe und Icon verwalten, damit Abos übersichtlich gruppiert werden.

**Acceptance Criteria:**
- [ ] `GET/POST/PUT/DELETE /api/v1/categories/`
- [ ] Kategorie hat: Name, Farbe (HEX), Icon (optional)
- [ ] Kategorie-Management Seite (Admin only)
- [ ] Farbige Badges in Abo-Liste angezeigt
- [ ] M2M-Verknüpfung Abo↔Kategorien im Web-Formular auswählbar

**Technical Notes:**
- Model `Category` + `subscription_categories` bereits vorhanden
- Neue Route: `GET /categories` mit Admin-Guard
- Abo-Formular: Checkbox-Gruppe für Kategorien

**Tests:** `tests/test_categories.py` (CRUD + M2M + tenant isolation)

**Dependencies:** STORY-004 (done)

---

#### STORY-012: Kategorie-Filter in Subscription-Liste
**Epic:** EPIC-002 | **Priority:** Should Have | **Points:** 3

**User Story:**
Als Benutzer möchte ich Abos nach Kategorie filtern, damit ich nur relevante Abos sehe.

**Acceptance Criteria:**
- [ ] `GET /api/v1/subscriptions/?category_id={id}` filtert korrekt
- [ ] Web-Abo-Liste: Dropdown "Nach Kategorie filtern"
- [ ] Filter kombinierbar mit Status + Billing-Cycle
- [ ] Kein Cross-Tenant Zugriff auf Kategorien möglich

**Technical Notes:**
- SQLAlchemy JOIN auf `subscription_categories`
- Query-Param `category_id` in `subscriptions.py`

**Tests:** `tests/test_subscriptions.py::test_filter_by_category_*`

**Dependencies:** STORY-011

---

#### STORY-013: Dark Mode Complete
**Epic:** EPIC-006 | **Priority:** Should Have | **Points:** 3

**User Story:**
Als Benutzer möchte ich zwischen Light und Dark Mode wechseln, damit ich die App komfortabel nutzen kann.

**Acceptance Criteria:**
- [ ] Toggle-Button in Navbar (Sonne/Mond-Icon)
- [ ] Theme-Wahl in `localStorage` gespeichert
- [ ] Theme wird VOR erstem Render gesetzt (kein Flash)
- [ ] System-Preference als Default
- [ ] Alle Seiten (Dashboard, Abos, Pläne, Login) im Dark Mode korrekt

**Technical Notes:**
- Inline `<script>` im `<head>` von base.html (vor Tailwind): liest localStorage
- `class="dark"` auf `<html>` gesetzt vor Paint
- Tailwind `darkMode: 'class'` bereits konfiguriert

**Tests:** `tests/test_web.py::test_dark_mode_cookie_*` (HTTP-Tests, kein Browser)

**Dependencies:** STORY-009 (done)

---

#### STORY-014: Multi-Currency Display + Tenant-Setting
**Epic:** EPIC-002 | **Priority:** Should Have | **Points:** 3

**User Story:**
Als Tenant-Admin möchte ich eine Standard-Währung konfigurieren und Abos in verschiedenen Währungen erfassen.

**Acceptance Criteria:**
- [ ] Tenant hat `currency`-Feld (default: EUR), editierbar in Settings
- [ ] Währungssymbole korrekt: € $ CHF £
- [ ] Dashboard zeigt Kosten gruppiert nach Währung wenn Mischung
- [ ] `GET /settings` + `POST /settings` für Tenant-Config

**Technical Notes:**
- Tenant-Settings Seite (Admin only)
- Währungs-Lookup-Dict in `app/core/currencies.py`

**Tests:** `tests/test_settings.py::test_currency_*`

---

#### STORY-015: Responsive Layout (Mobile + Hamburger)
**Epic:** EPIC-002 | **Priority:** Must Have | **Points:** 3

**User Story:**
Als mobiler Nutzer möchte ich die App ab 320px Viewport nutzen können.

**Acceptance Criteria:**
- [ ] Sidebar/Navbar: Hamburger-Menü auf Mobile (`< lg`)
- [ ] Tabellen: `overflow-x-auto` Container
- [ ] Buttons: `min-h-[44px]` Touch-Target
- [ ] Kein horizontaler Overflow bei 320px

**Technical Notes:**
- Alpine.js (CDN) für Hamburger-Toggle, oder Vanilla JS
- Tailwind `hidden lg:flex` Pattern in base.html

**Tests:** Visuelle Verifikation (kein pytest) — stattdessen Playwright-Smoke-Test optional

---

#### STORY-016: Logo + Session Secure Flag + Image Size
**Epic:** EPIC-001 | **Priority:** Must Have | **Points:** 2

**User Story:**
Als Benutzer möchte ich das mitKI.ai Logo sehen und sicher angemeldet sein.

**Acceptance Criteria:**
- [ ] Logo SVG in `static/images/logo.svg` + in Navbar + Login-Seite eingebunden
- [ ] `SessionMiddleware(https_only=settings.is_production)` gesetzt
- [ ] `IS_PRODUCTION=true` Env-Var in `.env.example` dokumentiert
- [ ] Docker-Image-Build: Größe < 500MB verifiziert (`docker images`)

**Tests:** `tests/test_auth.py::test_session_cookie_flags`

---

#### STORY-017: Staging Config + pyproject.toml + CI Pipeline
**Epic:** EPIC-001 | **Priority:** Must Have | **Points:** 3

**User Story:**
Als Developer möchte ich einen vollständigen CI/CD-Pipeline haben, damit jeder Push automatisch getestet wird.

**Acceptance Criteria:**
- [ ] `docker-compose.staging.yml` mit Port 8081 + eigenem DB-Volume
- [ ] `pyproject.toml` mit ruff + mypy Konfiguration
- [ ] `.github/workflows/ci.yml`: ruff → mypy → pytest --cov=app --cov-fail-under=70 → docker build
- [ ] `pre-commit` config (ruff + mypy als Hooks)
- [ ] `ruff check app/ tests/` ohne Fehler

**Technical Notes:**
- `[tool.ruff]` config: line-length=120, E/W/F/I rules
- `[tool.mypy]` config: ignore_missing_imports=true
- GitHub Actions: ubuntu-latest, python 3.12

**Tests:** CI läuft durch ohne Fehler

---

**Sprint 2 Total: 27 Points**

---

### 🔜 SPRINT 3 — Service Layer + Audit Log + In-App Notifications (23 Points)

**Sprint-Ziel:** Business Logic aus Routes in Services extrahieren. Audit Log schreibt jede Mutation. Benutzer sehen Benachrichtigungen im Dashboard.

**Liefert:** Professionelle Code-Architektur, vollständiges Audit-Trail, funktionierendes Notification-Center.

---

#### STORY-018: Service Layer Refactor
**Epic:** EPIC-002 | **Priority:** Must Have | **Points:** 5

**User Story:**
Als Developer möchte ich Business Logic in dedizierten Services haben, damit Routes schlank bleiben.

**Acceptance Criteria:**
- [ ] `app/services/subscription_service.py`: create, update, delete, list Methoden
- [ ] `app/services/plan_service.py`: CRUD
- [ ] `app/services/category_service.py`: CRUD
- [ ] Routes rufen nur noch Services auf (kein direktes `db.query()` in Routes)
- [ ] Alle bestehenden Tests weiterhin grün

**Technical Notes:**
- Services nehmen `db: Session, tenant_id: str` als Parameter
- Kein Breaking Change — gleiche Funktionalität, andere Struktur

**Tests:** Alle bestehenden Tests müssen weiterhin grün sein (Regression-Test)

---

#### STORY-019: Audit Log (Schreiben + Admin-View)
**Epic:** EPIC-006 | **Priority:** Should Have | **Points:** 5

**User Story:**
Als Admin möchte ich sehen, wer wann was geändert hat, damit ich Änderungen nachverfolgen kann.

**Acceptance Criteria:**
- [ ] `app/services/audit_service.py::log_action(db, tenant_id, user_id, action, entity_type, entity_id, old, new, ip)`
- [ ] Jedes Subscription-Create/Update/Delete loggt einen Eintrag
- [ ] `GET /audit-log` Seite (Admin only): tabellarische Anzeige
- [ ] Filter nach Zeitraum (letzte 7/30/90 Tage)
- [ ] Audit-Log-Einträge sind nicht löschbar (kein DELETE-Endpoint)

**Technical Notes:**
- Model `AuditLog` bereits vorhanden
- IP aus `request.client.host`
- Old/New Values als JSON-Diff

**Tests:** `tests/test_audit.py` (log on create/update/delete, no delete endpoint)

**Dependencies:** STORY-018

---

#### STORY-020: In-App Notifications (Service + Bell + Polling)
**Epic:** EPIC-003 | **Priority:** Should Have | **Points:** 5

**User Story:**
Als Benutzer möchte ich Benachrichtigungen im Dashboard sehen, damit ich nichts Wichtiges verpasse.

**Acceptance Criteria:**
- [ ] `app/services/notification_service.py::create(db, tenant_id, user_id, title, message, type, link)`
- [ ] Glocken-Icon in Navbar mit Unread-Badge (rote Zahl)
- [ ] Dropdown zeigt letzte 10 Notifications
- [ ] `POST /api/v1/notifications/{id}/read` markiert als gelesen
- [ ] `GET /api/v1/notifications/` gibt Unread-Count + Liste zurück
- [ ] Polling alle 60s via `setInterval` + fetch

**Technical Notes:**
- Model `Notification` bereits vorhanden
- Vanilla JS in `static/js/notifications.js`
- Notification wird bei jedem Subscription-Create angelegt

**Tests:** `tests/test_notifications.py` (create, list, mark-read, unread count)

**Dependencies:** STORY-018

---

#### STORY-021: Tests-Suite Basis (conftest + Fixtures + Coverage)
**Epic:** EPIC-001 | **Priority:** Must Have | **Points:** 5 (korrektur: 8)

**User Story:**
Als Developer möchte ich eine vollständige Test-Suite mit aussagekräftigen Fixtures haben.

**Acceptance Criteria:**
- [ ] `tests/conftest.py`: `TestClient`, In-Memory SQLite, Tenant-Fixtures (tenant_a, tenant_b, admin_user, regular_user)
- [ ] Fixture `auth_client(user)` loggt User ein und gibt TestClient zurück
- [ ] `pytest --cov=app --cov-report=term-missing` zeigt ≥ 70% Coverage
- [ ] Kritische Pfade (auth, isolation, CRUD): ≥ 90% Coverage
- [ ] Tests laufen in < 30 Sekunden

**Technical Notes:**
- `pytest-cov` in requirements
- Isolierte DB pro Test-Session (`StaticPool` + `create_all`)

**Tests:** `pytest tests/ -v` muss komplett grün sein

---

**Sprint 3 Total: 23 Points** (STORY-021: 8pts statt 5)

---

### 🔜 SPRINT 4 — E-Mail Notifications + Prefect Automation (22 Points)

**Sprint-Ziel:** Automatische E-Mail-Benachrichtigungen funktionieren. Prefect übernimmt täglich Renewal-Checks und Auto-Renewal.

**Liefert:** Vollautomatische Abo-Überwachung mit E-Mail-Alerts und Auto-Renewal-Logik.

---

#### STORY-022: E-Mail Service (SMTP + Jinja2 Templates)
**Epic:** EPIC-003 | **Priority:** Must Have | **Points:** 5

**User Story:**
Als Benutzer möchte ich E-Mails für wichtige Abo-Events erhalten.

**Acceptance Criteria:**
- [ ] `app/services/email_service.py` mit `send_email(to, subject, html_body)`
- [ ] SMTP via `aiosmtplib` (async), konfigurierbar per Env-Vars
- [ ] Jinja2 E-Mail-Templates: `templates/emails/renewal_reminder.html`, `welcome.html`, `renewed.html`
- [ ] Willkommens-E-Mail bei erfolgreicher Registrierung
- [ ] Env-Vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`

**Technical Notes:**
- `aiosmtplib` + `email.mime` für HTML-E-Mails
- Template-Rendering via `jinja2.Environment`
- Graceful Fail: SMTP nicht konfiguriert → only log warning

**Tests:** `tests/test_email.py` (Mock-SMTP via `aiosmtplib.testing`)

---

#### STORY-023: Prefect Flow: Renewal Reminder (täglich)
**Epic:** EPIC-003 | **Priority:** Must Have | **Points:** 5

**User Story:**
Als Benutzer möchte ich X Tage vor Abo-Verlängerung eine E-Mail erhalten.

**Acceptance Criteria:**
- [ ] Prefect Flow `renewal_reminder_flow` auf `automatisch.mitki.ai`
- [ ] Flow prüft täglich alle Abos mit `next_renewal <= today + notify_days_before`
- [ ] Pro Abo: E-Mail an `created_by` + In-App Notification
- [ ] Flow wird per `POST /api/v1/internal/trigger` + `INTERNAL_API_KEY` geschützt
- [ ] Tägliche Cron-Schedule: `0 8 * * *`

**Technical Notes:**
- `app/jobs/prefect_client.py`: HTTP-Trigger via `httpx`
- Prefect Deployment: `subscription_manager/flows/renewal_reminder.py`
- Internal-API-Key in Env-Var

**Tests:** `tests/test_jobs.py::test_renewal_check_logic` (Unit-Test der Check-Logik, ohne echten Prefect)

---

#### STORY-024: Prefect Flow: Auto-Renewal + Expiry Check
**Epic:** EPIC-003 | **Priority:** Should Have | **Points:** 5

**User Story:**
Als Benutzer möchte ich, dass Abos mit `auto_renew=true` automatisch verlängert werden.

**Acceptance Criteria:**
- [ ] Flow `auto_renew_flow`: `next_renewal` wird um einen Billing-Cycle vorgerückt
- [ ] Flow `expiry_check_flow`: Abos mit `end_date <= today` → Status `expired`
- [ ] Jede Auto-Aktion wird im Audit-Log erfasst
- [ ] Benachrichtigung (In-App + E-Mail) bei jeder automatischen Aktion

**Technical Notes:**
- Billing-Cycle-Logik: `monthly → +1 Monat`, `yearly → +1 Jahr`, `weekly → +7 Tage`
- Edge Cases: End-of-Month (30. Feb → 28. Feb)

**Tests:** `tests/test_jobs.py::test_auto_renewal_*` (Unit-Tests der Logik)

**Dependencies:** STORY-022, STORY-023

---

#### STORY-025: Internal API Endpoints (Prefect-Trigger)
**Epic:** EPIC-003 | **Priority:** Must Have | **Points:** 3

**Acceptance Criteria:**
- [ ] `POST /api/v1/internal/renewal-check` (geschützt per `X-Internal-Key`)
- [ ] `POST /api/v1/internal/auto-renew`
- [ ] `POST /api/v1/internal/expiry-check`
- [ ] Alle 3 Endpoints geben Job-Ergebnis als JSON zurück
- [ ] Falscher Key → HTTP 403

**Tests:** `tests/test_internal_api.py`

---

**Sprint 4 Total: 18 Points**

---

### 🔜 SPRINT 5 — Teams + Self-Service + Onboarding (26 Points)

**Sprint-Ziel:** Mehrere Benutzer pro Tenant. Admins können einladen und verwalten. Neue Tenants werden durch einen Wizard geführt.

**Liefert:** Vollständiges Team-Management, Self-Service-Portal, Onboarding-Wizard.

---

#### STORY-026: Team Invitations (E-Mail + Registrierungs-Link)
**Epic:** EPIC-004 | **Priority:** Should Have | **Points:** 8

**User Story:**
Als Admin möchte ich Teammitglieder per E-Mail einladen, damit sie Zugriff auf unsere Abos bekommen.

**Acceptance Criteria:**
- [ ] `POST /api/v1/users/invite`: E-Mail + Rolle → Einladungs-E-Mail mit Token-Link
- [ ] Einladungstoken: UUID, 48h gültig, in `team_invitations` gespeichert
- [ ] `GET /register?token={token}`: Registrierungsformular mit vorausgefüllter E-Mail
- [ ] Nach Registrierung: User automatisch zum einladenden Tenant zugeordnet
- [ ] Abgelaufene/genutzte Tokens → HTTP 410 Gone

**Technical Notes:**
- Model `TeamInvitation` neu anlegen
- E-Mail-Template: `templates/emails/invitation.html`

**Tests:** `tests/test_teams.py::test_invite_flow_*`

**Dependencies:** STORY-022

---

#### STORY-027: User Management Seite (Admin)
**Epic:** EPIC-004 | **Priority:** Should Have | **Points:** 3

**Acceptance Criteria:**
- [ ] `GET /users` (Admin only): Team-Mitglieder-Liste mit Rolle + letztem Login
- [ ] `PUT /api/v1/users/{id}`: Rolle ändern (Admin only)
- [ ] `DELETE /api/v1/users/{id}`: User deaktivieren (kein Login mehr), kein Hard-Delete
- [ ] Eigener Account kann nicht deaktiviert werden

**Tests:** `tests/test_teams.py::test_user_management_*`

---

#### STORY-028: Self-Service Portal (Profil + Passwort + Abo-Kündigung)
**Epic:** EPIC-004 | **Priority:** Should Have | **Points:** 5

**User Story:**
Als Benutzer möchte ich mein Profil und Passwort selbst verwalten und Abos kündigen können.

**Acceptance Criteria:**
- [ ] `GET/POST /profile`: Name + E-Mail ändern
- [ ] `POST /profile/password`: Passwort ändern (altes Passwort als Verifikation)
- [ ] Abo-Detailseite: "Abo kündigen" Button mit Bestätigungs-Dialog
- [ ] Kündigung setzt Status auf `cancelled` + Audit-Log-Eintrag
- [ ] Profil-Änderungen im Audit-Log

**Tests:** `tests/test_profile.py`

---

#### STORY-029: Onboarding Wizard (3-Step, einmalig)
**Epic:** EPIC-004 | **Priority:** Should Have | **Points:** 5

**User Story:**
Als neuer Tenant-Admin möchte ich durch die Einrichtung geführt werden, damit ich schnell loslegen kann.

**Acceptance Criteria:**
- [ ] Wizard erscheint nach erstem Login wenn `tenant.onboarding_complete = False`
- [ ] Step 1: Organisationsname + Standard-Währung + Locale
- [ ] Step 2: Optionale Team-Einladung (überspringbar)
- [ ] Step 3: Erstes Abo anlegen (mit Demo-Vorlage)
- [ ] "Überspringen"-Button auf jedem Step
- [ ] Nach Abschluss: `tenant.onboarding_complete = True`

**Technical Notes:**
- `onboarding_complete: bool` Feld zum Tenant-Model hinzufügen
- Multi-Step-Formular als separate Route `/onboarding/{step}`

**Tests:** `tests/test_onboarding.py`

**Dependencies:** STORY-026 (für Team-Einladung in Step 2)

---

#### STORY-030: Settings Seite (Tenant + Locale)
**Epic:** EPIC-004 | **Priority:** Should Have | **Points:** 3

**Acceptance Criteria:**
- [ ] `GET/POST /settings` (Admin only): Org-Name, Währung, Locale, Timezone
- [ ] Änderungen sofort wirksam (Session-Refresh)
- [ ] Audit-Log-Eintrag bei Settings-Änderungen

**Tests:** `tests/test_settings.py`

---

**Sprint 5 Total: 24 Points**

---

### 🔜 SPRINT 6 — Volltextsuche + i18n + Import/Export + Icons (29 Points)

**Sprint-Ziel:** Suche, Mehrsprachigkeit, Daten-Portabilität und Icon-Bibliothek.

**Liefert:** Vollständig internationalisierte App, Bulk-Import für Migration, Icon-Picker im Abo-Formular.

---

#### STORY-031: FTS5 Volltextsuche
**Epic:** EPIC-005 | **Priority:** Should Have | **Points:** 5

**User Story:**
Als Benutzer möchte ich nach Abos suchen, damit ich schnell das Richtige finde.

**Acceptance Criteria:**
- [ ] `app/services/search_service.py`: SQLite FTS5 Virtual Table `subscriptions_fts`
- [ ] Suche über: Name, Anbieter, Notizen
- [ ] `GET /api/v1/search/?q={query}` gibt Top-10 Ergebnisse zurück
- [ ] Suchleiste in Navbar: Debounced fetch (300ms) mit Dropdown-Ergebnissen
- [ ] FTS5-Code vollständig in `search_service.py` isoliert (PostgreSQL Migration-Pfad)

**Technical Notes:**
- FTS5 Virtual Table via `CREATE VIRTUAL TABLE subscriptions_fts USING fts5(...)`
- Trigger oder manuelles Sync nach Insert/Update
- Vanilla JS + `fetch('/api/v1/search/?q=...')` mit Debounce

**Tests:** `tests/test_search.py` (insert + search, FTS5 ranking)

---

#### STORY-032: CSV Import (Upload + Spalten-Mapping)
**Epic:** EPIC-005 | **Priority:** Should Have | **Points:** 5

**User Story:**
Als Benutzer möchte ich meine Abos aus einer CSV-Datei importieren.

**Acceptance Criteria:**
- [ ] `POST /subscriptions/import` (Multipart-Upload)
- [ ] Vorschau: Erste 5 Zeilen + Spalten-Mapping UI
- [ ] Spalten-Mapping: Quell-Spalte → Ziel-Feld (Dropdown)
- [ ] Import-Bericht: X erfolgreich, Y fehlgeschlagen (mit Gründen)
- [ ] Duplikate (gleicher Name + Provider) werden übersprungen

**Technical Notes:**
- `python-multipart` für File-Upload (bereits in requirements?)
- `csv` stdlib für Parsing
- Zwei-Step: Upload → Mapping-Form → Confirm → Import

**Tests:** `tests/test_import_export.py::test_csv_import_*`

---

#### STORY-033: CSV + JSON Export
**Epic:** EPIC-005 | **Priority:** Should Have | **Points:** 3

**Acceptance Criteria:**
- [ ] `GET /api/v1/subscriptions/export?format=csv` → CSV-Download
- [ ] `GET /api/v1/subscriptions/export?format=json` → JSON-Download
- [ ] Export-Button in Web-UI
- [ ] Export berücksichtigt aktive Filter (Status, Kategorie)
- [ ] JSON-Import für vollständiges Restore

**Tests:** `tests/test_import_export.py::test_export_*`

---

#### STORY-034: Internationalisierung DE + EN
**Epic:** EPIC-005 | **Priority:** Should Have | **Points:** 8

**User Story:**
Als englischsprachiger Nutzer möchte ich die App auf Englisch nutzen können.

**Acceptance Criteria:**
- [ ] `translations/de.json` + `translations/en.json` mit allen UI-Strings
- [ ] Sprach-Switcher Dropdown in Navbar (DE/EN Flag-Icons)
- [ ] Sprache wird in `user.locale` gespeichert
- [ ] Jinja2 Template: `{{ _("key") }}` Pattern via Custom Filter
- [ ] Fallback: Accept-Language Header wenn User-Locale nicht gesetzt
- [ ] Datumsformat lokalisiert (DE: 29.03.2026, EN: 03/29/2026)

**Technical Notes:**
- Eigene `i18n_middleware.py` in `app/core/`
- `Jinja2Templates.env.globals["_"] = translate_func`
- Keine externe i18n-Library (Babel) — einfaches JSON-Dict reicht

**Tests:** `tests/test_i18n.py` (translation lookup, fallback, locale switch)

---

#### STORY-035: Icon Bibliothek (Picker + Service)
**Epic:** EPIC-006 | **Priority:** Should Have | **Points:** 8

**User Story:**
Als Benutzer möchte ich beim Erstellen eines Abos ein passendes Icon auswählen.

**Acceptance Criteria:**
- [ ] `app/services/icon_service.py`: Lädt Icons aus `static/icons/` (lokal) mit Metadaten
- [ ] `GET /api/v1/icons/?q={query}` sucht Icons nach Name/Tag
- [ ] Icon-Picker im Abo-Formular: Grid + Suche + Auswahl
- [ ] Ausgewähltes Icon in Abo-Liste und Dashboard angezeigt
- [ ] Mindestens 50 SaaS-Icons (SVG) in `static/icons/`
- [ ] `Subscription.icon_id` Feld (nullable)

**Technical Notes:**
- Icons aus Simpleicons.org (freie SVG-Bibliothek) oder Heroicons
- Metadaten in `static/icons/manifest.json`
- NocoDB-Integration kommt in Sprint 7 (FR-037)

**Tests:** `tests/test_icons.py` (icon list, search, icon on subscription)

---

**Sprint 6 Total: 29 Points**

---

### 🔜 SPRINT 7 — Admin Analytics + Webhooks + Coupons + Custom Fields (28 Points)

**Sprint-Ziel:** Admin bekommt vollständiges Analytics-Dashboard. Webhooks ermöglichen Drittanbieter-Integration. NocoDB wird für Icon-Verwaltung angebunden.

---

#### STORY-036: Admin Analytics Dashboard (MRR, Churn, Charts)
**Epic:** EPIC-006 | **Priority:** Should Have | **Points:** 8

**User Story:**
Als Admin möchte ich KPI-Charts zur Umsatz- und Churn-Entwicklung sehen.

**Acceptance Criteria:**
- [ ] `app/services/analytics_service.py`: MRR, Churn, Revenue-Timeline
- [ ] MRR = Summe aller aktiven Abos normalisiert auf Monat
- [ ] Churn-Rate = cancelled / (cancelled + active) im Zeitraum
- [ ] Line-Chart: Revenue letzte 12 Monate
- [ ] Bar-Chart: Neue vs. gekündigte Abos pro Monat
- [ ] Nur Admin-Rolle sichtbar

**Tests:** `tests/test_analytics.py` (MRR-Berechnung, Churn-Formel)

---

#### STORY-037: Outgoing Webhooks (HMAC + Prefect Delivery)
**Epic:** EPIC-007 | **Priority:** Could Have | **Points:** 8

**User Story:**
Als Entwickler möchte ich Webhook-Benachrichtigungen bei Abo-Events empfangen.

**Acceptance Criteria:**
- [ ] `GET/POST/DELETE /api/v1/webhooks/` Endpoint-Verwaltung
- [ ] Events: `subscription.created`, `subscription.updated`, `subscription.cancelled`, `subscription.renewed`
- [ ] HMAC-SHA256 Signatur im `X-Webhook-Signature` Header
- [ ] Prefect Flow: 3 Retry-Versuche mit Exponential Backoff
- [ ] Delivery-Log mit HTTP-Status-Codes
- [ ] Test-Button im UI löst manuell Event aus

**Technical Notes:**
- Modelle `WebhookEndpoint` + `WebhookDelivery` neu anlegen
- Prefect: `webhook_delivery_flow` via Internal API getriggert

**Tests:** `tests/test_webhooks.py` (HMAC-Berechnung, Endpoint-CRUD)

---

#### STORY-038: Coupons + Rabattcodes
**Epic:** EPIC-007 | **Priority:** Could Have | **Points:** 5

**Acceptance Criteria:**
- [ ] `Coupon` Model: Code, Typ (percent/fixed), Wert, Gültigkeitszeitraum, max_uses
- [ ] `GET/POST/PUT /api/v1/coupons/` (Admin only)
- [ ] `POST /api/v1/coupons/validate` prüft Code + gibt Rabatt zurück
- [ ] Coupon bei Abo-Erstellung anwendbar → Kosten anpassen
- [ ] `use_count` wird bei Nutzung inkrementiert

**Tests:** `tests/test_coupons.py`

---

#### STORY-039: Custom Fields (Definition + Dynamisches Formular)
**Epic:** EPIC-007 | **Priority:** Could Have | **Points:** 5

**Acceptance Criteria:**
- [ ] Admin definiert Custom Fields: Name, Typ (text/number/date/select), Optionen
- [ ] Felder erscheinen dynamisch im Abo-Formular
- [ ] Werte in `subscription.custom_fields_json` gespeichert
- [ ] Custom Fields in Abo-Detail-Ansicht sichtbar
- [ ] Custom Fields im CSV-Export enthalten

**Tests:** `tests/test_custom_fields.py`

---

#### STORY-040: NocoDB Icon-Integration (REST + Cache)
**Epic:** EPIC-007 | **Priority:** Could Have | **Points:** 3

**Acceptance Criteria:**
- [ ] `icon_service.py` erweitert: Icons aus NocoDB REST API abrufen
- [ ] Lokaler Cache (In-Memory, TTL 60min) mit `functools.lru_cache`-ähnlichem Pattern
- [ ] Fallback auf `static/icons/` wenn NocoDB nicht erreichbar
- [ ] Admin kann Cache via `POST /api/v1/icons/sync` leeren + neu laden

**Tests:** `tests/test_icons.py::test_nocodb_fallback` (Mock NocoDB mit `respx`)

---

**Sprint 7 Total: 29 Points**

---

### 🔜 SPRINT 8 — Security Upgrade + Logging + JWT (24 Points)

**Sprint-Ziel:** App bekommt JWT-Auth, SSO-Login und strukturiertes Logging für Production-Monitoring.

---

#### STORY-041: Structured Logging (structlog + Request-ID)
**Epic:** EPIC-006 | **Priority:** Could Have | **Points:** 3

**Acceptance Criteria:**
- [ ] `app/core/middleware.py`: Request-ID Middleware (UUID per Request)
- [ ] `structlog` konfiguriert: JSON-Lines Format
- [ ] Request-ID in jedem Log-Eintrag
- [ ] Log-Level via `LOG_LEVEL` Env-Var
- [ ] Loki-kompatibler Output

**Tests:** `tests/test_middleware.py::test_request_id_*`

---

#### STORY-042: OAuth2/JWT Auth Upgrade
**Epic:** EPIC-008 | **Priority:** Could Have | **Points:** 8

**User Story:**
Als API-Client möchte ich mit Bearer-Token authentifizieren können.

**Acceptance Criteria:**
- [ ] `POST /api/v1/auth/token` → Access Token (15min) + Refresh Token (7 Tage)
- [ ] `POST /api/v1/auth/refresh` → neues Access Token
- [ ] `get_current_user()` unterstützt Bearer Token UND Session-Cookie
- [ ] Web-UI nutzt weiterhin Session-Cookie (keine Breaking Change)
- [ ] Token-Blacklist bei Logout (In-Memory Set, TTL)

**Technical Notes:**
- `python-jose` für JWT
- `app/core/jwt.py`: create_access_token, verify_token

**Tests:** `tests/test_auth.py::test_jwt_*`

---

#### STORY-043: SSO Integration (Google + Microsoft)
**Epic:** EPIC-008 | **Priority:** Could Have | **Points:** 8

**User Story:**
Als Benutzer möchte ich mich mit Google oder Microsoft einloggen können.

**Acceptance Criteria:**
- [ ] "Login mit Google" Button auf Login-Seite
- [ ] "Login mit Microsoft" Button auf Login-Seite
- [ ] OIDC-Flow via `Authlib` Library
- [ ] Neuer Account bei erstem SSO-Login automatisch erstellt
- [ ] Bestehender Account (gleiche E-Mail) wird verknüpft
- [ ] SSO-Provider per Tenant aktivierbar/deaktivierbar

**Technical Notes:**
- `authlib` + `httpx` für OIDC
- Callback: `GET /auth/callback/google`, `/auth/callback/microsoft`

**Tests:** `tests/test_auth.py::test_sso_*` (Mock OAuth2-Endpunkte)

**Dependencies:** STORY-042

---

#### STORY-044: Alembic Migrations Setup
**Epic:** EPIC-008 | **Priority:** Could Have | **Points:** 3

**Acceptance Criteria:**
- [ ] `alembic init migrations` durchgeführt
- [ ] `alembic.ini` konfiguriert (DATABASE_URL aus Env)
- [ ] Erste Migration: Schema-Dump des aktuellen Zustands
- [ ] `alembic upgrade head` läuft ohne Fehler
- [ ] CI prüft Migration-Konsistenz

**Tests:** `tests/test_migrations.py::test_alembic_head_*`

---

**Sprint 8 Total: 22 Points**

---

### 🔜 SPRINT 9 — GraphQL + YouTube + PostgreSQL + Launch (23 Points)

**Sprint-Ziel:** GraphQL API als zweiter API-Layer. Landing Page für YouTube. PostgreSQL-Migration validiert. Security Review.

---

#### STORY-045: GraphQL API (Strawberry)
**Epic:** EPIC-008 | **Priority:** Could Have | **Points:** 8

**Acceptance Criteria:**
- [ ] `POST /graphql` Endpoint via `strawberry-graphql`
- [ ] Queries: `subscriptions`, `plans`, `categories`, `me`
- [ ] Mutations: `createSubscription`, `updateSubscription`, `deleteSubscription`
- [ ] Auth: gleicher Mechanismus wie REST (Session/Bearer)
- [ ] GraphQL Playground unter `/graphql` im DEV-Modus

**Tests:** `tests/test_graphql.py` (Queries + Mutations)

---

#### STORY-046: YouTube Showcase (Landing Page + Demo-Daten)
**Epic:** EPIC-009 | **Priority:** Could Have | **Points:** 5

**Acceptance Criteria:**
- [ ] `GET /` Landing Page (unauthenticated) mit Feature-Highlights
- [ ] `scripts/seed.py` erweitert: Demo-Tenant "Acme GmbH" mit 20 realistischen Abos
- [ ] Demo-Dashboard ist visuell ansprechend für Video-Aufnahmen
- [ ] Landing Page zeigt Screenshots / Feature-Cards

**Tests:** `tests/test_web.py::test_landing_page`

---

#### STORY-047: PostgreSQL Migration Validation
**Epic:** EPIC-008 | **Priority:** Could Have | **Points:** 5

**Acceptance Criteria:**
- [ ] `docker-compose.postgres.yml`: App + PostgreSQL Container
- [ ] `DATABASE_URL=postgresql://...` funktioniert ohne Code-Änderungen
- [ ] `search_service.py` auf `tsvector` + GIN Index umgestellt (PostgreSQL-Pfad)
- [ ] Alle Tests laufen gegen PostgreSQL durch
- [ ] CI: optionaler Job `test-postgres`

**Technical Notes:**
- Alembic-Migration ist dialect-aware
- `IF_POSTGRES` Guard in `search_service.py`

**Tests:** `pytest tests/ --db=postgres` (via `conftest.py` Fixture)

---

#### STORY-048: Security Review + Load Test
**Epic:** EPIC-008 | **Priority:** Must Have | **Points:** 3

**Acceptance Criteria:**
- [ ] OWASP Top 10 Checklistee manuell durchgegangen und dokumentiert
- [ ] Locust Load Test: 50 concurrent users, p95 < 500ms bestätigt
- [ ] Security Headers via Caddy konfiguriert (HSTS, X-Frame-Options etc.)
- [ ] `bandit app/` ohne High-Severity Findings

**Tests:** `locust -f tests/locustfile.py --headless -u 50 -r 10 --run-time 60s`

---

**Sprint 9 Total: 21 Points**

---

## Sprint Allocation Übersicht

| Sprint | Ziel | Stories | Points | Status |
|--------|------|---------|--------|--------|
| **Sprint 1** | MVP Baseline (Auth, CRUD, Docker) | STORY-001–009 | 37 | ✅ Done |
| **Sprint 2** | Dashboard + Kategorien + Responsive | STORY-010–017 | 27 | 🔜 Next |
| **Sprint 3** | Service Layer + Audit + Notifications | STORY-018–021 | 23 | Pending |
| **Sprint 4** | E-Mail + Prefect Automation | STORY-022–025 | 18 | Pending |
| **Sprint 5** | Teams + Self-Service + Onboarding | STORY-026–030 | 24 | Pending |
| **Sprint 6** | Suche + i18n + Import/Export + Icons | STORY-031–035 | 29 | Pending |
| **Sprint 7** | Analytics + Webhooks + Coupons + NocoDB | STORY-036–040 | 29 | Pending |
| **Sprint 8** | Security + JWT + SSO + Logging | STORY-041–044 | 22 | Pending |
| **Sprint 9** | GraphQL + YouTube + PostgreSQL + Launch | STORY-045–048 | 21 | Pending |
| **Total** | | **48 Stories** | **230 Points** | |

---

## Epic Traceability

| Epic ID | Epic Name | Stories | Points | Sprints |
|---------|-----------|---------|--------|---------|
| EPIC-001 | Core Platform & Auth | 001–003, 007–009, 016–017, 021, 044 | 30 | S1–S3, S8 |
| EPIC-002 | Subscription Management | 004–005, 010–015 | 35 | S1–S2 |
| EPIC-003 | Notifications & Automation | 020, 022–025 | 23 | S3–S4 |
| EPIC-004 | Self-Service & Teams | 026–030 | 24 | S5 |
| EPIC-005 | Search, i18n & Data Mgmt | 031–034 | 21 | S6 |
| EPIC-006 | Admin Dashboard & Quality | 006, 019, 036, 041 | 19 | S1, S3, S7–S8 |
| EPIC-007 | Integrations | 037–040 | 21 | S7 |
| EPIC-008 | Security Upgrade | 042–045, 047–048 | 27 | S8–S9 |
| EPIC-009 | YouTube & Launch | 046 | 5 | S9 |

---

## FR → Story Mapping

| FR | Story | Sprint |
|----|-------|--------|
| FR-001 | STORY-001 | ✅ S1 |
| FR-002 | STORY-002 | ✅ S1 |
| FR-003 | STORY-003 | ✅ S1 |
| FR-004 | STORY-004, 012 | ✅ S1, S2 |
| FR-005 | STORY-005 | ✅ S1 |
| FR-006 | STORY-010 | S2 |
| FR-007 | STORY-006 | ✅ S1 |
| FR-008 | STORY-007 | ✅ S1 |
| FR-009 | STORY-008, 016 | ✅ S1, S2 |
| FR-010 | STORY-022, 025 | S4 |
| FR-011 | STORY-009, 016 | ✅ S1, S2 |
| FR-012 | STORY-015 | S2 |
| FR-013 | STORY-028 | S5 |
| FR-014 | STORY-036 | S7 |
| FR-015 | STORY-019 | S3 |
| FR-016 | STORY-020 | S3 |
| FR-017 | STORY-024 | S4 |
| FR-018 | STORY-026, 027 | S5 |
| FR-019 | STORY-011, 012 | S2 |
| FR-020 | STORY-013 | S2 |
| FR-021 | STORY-031 | S6 |
| FR-022 | STORY-032, 033 | S6 |
| FR-023 | STORY-034 | S6 |
| FR-024 | STORY-029 | S5 |
| FR-025 | STORY-014 | S2 |
| FR-026 | STORY-037 | S7 |
| FR-027 | STORY-038 | S7 |
| FR-028 | STORY-043 | S8 |
| FR-029 | STORY-045 | S9 |
| FR-030 | STORY-039 | S7 |
| FR-031 | STORY-042 | S8 |
| FR-032 | STORY-041 | S8 |
| FR-033 | STORY-046 | S9 |
| FR-034 | STORY-017 | S2 |
| FR-035 | STORY-044, 047 | S8–S9 |
| FR-036 | STORY-035 | S6 |
| FR-037 | STORY-040 | S7 |

**Alle 37 FRs abgedeckt ✅**

---

## Risiken + Mitigation

**Hoch:**
- **Prefect-Abhängigkeit** (FR-010, FR-017): Prefect LXC 109 muss erreichbar sein für E-Mail-Tests → Mitigation: Unit-Tests mocken Prefect, Integration-Tests optional
- **Session-Limit-Breaks**: Große Stories (8pts) können Session-Kontext sprengen → Mitigation: Stories bei Bedarf in Substories aufteilen

**Mittel:**
- **SMTP-Konfiguration**: Kein SMTP-Server konfiguriert → Mitigation: Story-022 hat Graceful-Fail, Tests mocken SMTP
- **SQLite Concurrent Writes**: WAL-Mode ausreichend für 50 User → Bei Wachstum: Sprint 9 PostgreSQL-Migration

**Gering:**
- **NocoDB API-Änderungen** (FR-037): NocoDB-API ändert sich → Mitigation: Fallback auf lokale Icons

---

## Definition of Done (DoD)

Jede Story gilt als **Done** wenn:
- [ ] Code implementiert und committed
- [ ] `pytest tests/ -v` — alle Tests für diese Story grün
- [ ] `pytest --cov=app` — Coverage für geänderte Module ≥ 80%
- [ ] `ruff check app/ tests/` — kein Fehler
- [ ] Acceptance Criteria im PRD abgehakt (`[x]`)
- [ ] Docker-Build erfolgreich (`docker compose build`)
- [ ] Kurze manuelle Verifikation (Demo der Funktion)

---

## Nächster Schritt

**Sprint 2 starten:** STORY-010 bis STORY-017

Empfohlene Story-Reihenfolge innerhalb Sprint 2:
1. **STORY-017** (CI-Pipeline) — zuerst, damit alle weiteren Stories automatisch getestet werden
2. **STORY-011** (Kategorien CRUD) — Basis für STORY-012
3. **STORY-012** (Kategorie-Filter)
4. **STORY-010** (Dashboard Charts)
5. **STORY-013** (Dark Mode)
6. **STORY-014** (Multi-Currency)
7. **STORY-015** (Responsive)
8. **STORY-016** (Logo + Secure Flag)

---

*Sprint Plan erstellt mit BMAD Method v6 — Phase 4 (Implementation Planning)*
