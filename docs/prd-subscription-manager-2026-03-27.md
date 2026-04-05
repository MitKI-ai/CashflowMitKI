# Product Requirements Document: Subscription Manager

**Date:** 2026-03-27 · **Last Updated:** 2026-03-30
**Author:** Eddy
**Version:** 2.0
**Project Type:** Web Application (SaaS)
**Project Level:** Level 3 (12-40 Stories)
**Status:** Implementation Complete — All 9 Sprints / 48 Stories / 230 Points Delivered

---

## Implementation Status (2026-03-30)

| Metric | Zielwert | Aktuell |
|--------|----------|---------|
| Test Coverage | ≥ 70% | **89%** (247 Tests, alle grün) |
| Story Points delivered | 230 | **230 / 230 (100%)** |
| Sprints completed | 9 | **9 / 9** |
| FRs implemented | 37 | **~34 / 37 vollständig, 3 teilweise** |
| API Endpoints | — | **55+ REST + GraphQL** |
| Neue Dependencies | — | structlog, PyJWT, authlib, strawberry-graphql, alembic |

**Teilweise implementiert (Gaps):**
- FR-016: Notifications-Seite fehlt noch (nur Dropdown)
- FR-026: Webhook Retry-Logic und Delivery-Log noch offen
- FR-031: JWT Refresh Token fehlt; Web-Session nutzt noch User-ID, kein JWT im Cookie

---

## Document Overview

This Product Requirements Document (PRD) defines the functional and non-functional requirements for the Subscription Manager SaaS platform by mitKI.ai. It serves as the source of truth for what will be built and provides traceability from requirements through implementation.

**Related Documents:**
- Vision: `docs/vision.md`
- Infrastructure: `docs/infrastructure.md`
- Implementation Plan: `docs/implementation-plan.md`
- Branding: `branding.md`

---

## Executive Summary

Der Subscription Manager ist ein Multi-Tenant SaaS-Produkt von mitKI.ai zur Verwaltung von Abonnements. Er dient gleichzeitig als echtes Produkt für B2B-Kunden und als YouTube-Showcase für den mitKI.ai-Kanal. Die Plattform ermöglicht es Unternehmen, ihre Abonnements zentral zu verwalten, Kosten zu tracken, Teams einzubinden und durch Automatisierung Verwaltungsaufwand zu reduzieren.

Tech-Stack: FastAPI + Jinja2 SSR + Tailwind CSS + SQLite + Docker + Coolify auf Proxmox.

---

## Product Goals

### Business Objectives

1. **Marktpositionierung:** Ein funktionsfähiges SaaS-Produkt für Abo-Verwaltung am Markt positionieren
2. **Markenstärkung:** mitKI.ai als Marke durch ein öffentliches Showcase-Projekt stärken (YouTube-Content)
3. **Self-Service Platform:** Multi-Tenant-Plattform mit Self-Service für Kunden bereitstellen

### Success Metrics

| Metrik | Zielwert | Zeitrahmen |
|--------|----------|------------|
| MVP deployed auf Coolify | Funktionierend mit `/health` | Phase 1 (Woche 6) |
| Test-Tenants aktiv | ≥ 3 Tenants auf Staging | Phase 2 (Woche 10) |
| Feature-Completion | Alle 36 Ja-Features | Phase 5 (Woche 22) |
| YouTube Demo | Video auf Basis des Produkts | Phase 5 |
| Test Coverage | ≥ 70% | Fortlaufend |

---

## Functional Requirements

Functional Requirements (FRs) define **what** the system does - specific features and behaviors.

Each requirement includes:
- **ID**: Unique identifier (FR-001, FR-002, etc.)
- **Priority**: Must Have / Should Have / Could Have (MoSCoW)
- **Description**: What the system should do
- **Acceptance Criteria**: How to verify it's complete

---

### FR-001: Multi-Tenant Isolation

**Priority:** Must Have

**Description:**
Jeder Kunde (Organisation) erhält einen isolierten Tenant. Alle Daten sind durch `tenant_id` getrennt. Kein Datenzugriff über Tenant-Grenzen hinweg möglich.

**Acceptance Criteria:**
- [x] Jeder API-Call filtert automatisch nach `tenant_id`
- [x] Ein User kann nur Daten seines eigenen Tenants sehen
- [x] Datenbank-Queries enthalten immer einen `tenant_id` Filter
- [ ] Tenant hat eigenen `slug` für URL-Routing

**Dependencies:** Keine

---

### FR-002: User Authentication

**Priority:** Must Have

**Description:**
Benutzer können sich mit E-Mail und Passwort anmelden. Sessions werden über signierte Cookies verwaltet. Später Upgrade auf OAuth2/JWT (siehe FR-031).

**Acceptance Criteria:**
- [x] Login mit E-Mail + Passwort funktioniert
- [x] Passwörter werden mit bcrypt gehasht gespeichert
- [x] Session-Cookie ist HTTP-Only, Secure, SameSite
- [x] Logout invalidiert die Session
- [x] Fehlgeschlagene Logins zeigen generische Fehlermeldung

**Dependencies:** FR-001

---

### FR-003: Rollenbasierte Zugriffskontrolle (RBAC)

**Priority:** Must Have

**Description:**
Drei Rollen pro Tenant: Admin (voller Zugriff), User (CRUD eigene Abos, Dashboard), Viewer (nur Lesen). Rollen werden bei User-Erstellung zugewiesen.

**Acceptance Criteria:**
- [x] Admin kann alles: User verwalten, Einstellungen, alle Abos
- [x] User kann eigene Abos erstellen/bearbeiten, Dashboard sehen
- [x] Viewer kann nur lesen, keine Änderungen
- [x] Zugriffsverletzung gibt HTTP 403 zurück
- [x] Rolle wird in Session/Token mitgeführt

**Dependencies:** FR-001, FR-002

---

### FR-004: Subscription CRUD

**Priority:** Must Have

**Description:**
Abonnements erstellen, lesen, bearbeiten und löschen. Felder: Name, Anbieter, Kosten, Währung, Billing-Zyklus, Status, Start-/Enddatum, Auto-Renewal, Notizen.

**Acceptance Criteria:**
- [x] Abo erstellen mit allen Pflichtfeldern
- [x] Abo bearbeiten (alle Felder änderbar)
- [x] Abo löschen (Soft-Delete oder Hard-Delete)
- [x] Abo-Liste mit Sortierung (Name, Kosten, Verlängerungsdatum)
- [x] Abo-Liste mit Filterung (Status, Kategorie)
- [x] Abo-Detailansicht mit allen Informationen

**Dependencies:** FR-001, FR-003

---

### FR-005: Plan Management

**Priority:** Must Have

**Description:**
Tenant-Admins können Abo-Plan-Vorlagen definieren (z.B. "Monthly Basic", "Yearly Pro"). Pläne haben: Name, Beschreibung, Preis, Währung, Billing-Zyklus, Features-Liste.

**Acceptance Criteria:**
- [x] Plan erstellen mit Name, Preis, Zyklus
- [x] Plan bearbeiten und deaktivieren
- [x] Plan als Vorlage bei Abo-Erstellung auswählbar
- [x] Features-Liste als JSON-Array speicherbar
- [x] Sortierung per `sort_order`

**Dependencies:** FR-001, FR-003

---

### FR-006: Web Dashboard

**Priority:** Must Have

**Description:**
Übersichts-Dashboard mit KPIs: Gesamtkosten (monatlich), aktive Abos, anstehende Verlängerungen (7/30 Tage), Kosten-Breakdown nach Kategorie. Charts via Chart.js.

**Acceptance Criteria:**
- [x] Summary-Cards: monatliche Gesamtkosten, aktive Abo-Anzahl
- [x] Anstehende Verlängerungen (nächste 7 und 30 Tage)
- [x] Kosten-Balkendiagramm (nach Billing-Cycle, Chart.js)
- [x] Status-Breakdown (Doughnut-Chart)
- [ ] Dashboard lädt in < 2 Sekunden (NFR-002)

**Dependencies:** FR-004, FR-005

---

### FR-007: Public REST API

**Priority:** Must Have

**Description:**
Öffentliche REST API unter `/api/v1/` mit allen CRUD-Operationen. Auto-generierte OpenAPI/Swagger Dokumentation unter `/docs`.

**Acceptance Criteria:**
- [x] Alle Entitäten über REST API erreichbar
- [x] JSON Request/Response Format
- [x] Pagination für Listen-Endpoints
- [x] Swagger UI unter `/docs` erreichbar
- [x] Konsistentes Error-Response Format
- [x] API-Versionierung (v1)

**Dependencies:** FR-001, FR-002

---

### FR-008: Health/Metrics Endpoints

**Priority:** Must Have

**Description:**
`GET /health` gibt Systemstatus zurück. `GET /metrics` gibt Key-Metriken als JSON zurück (für Monitoring/Grafana).

**Acceptance Criteria:**
- [x] `/health` gibt `{"status": "ok", "version": "x.y.z"}` zurück
- [x] `/health` prüft DB-Verbindung
- [x] `/metrics` gibt aktive Tenants, User-Count, Abo-Count zurück
- [x] Beide Endpoints ohne Authentifizierung erreichbar
- [x] Response < 100ms

**Dependencies:** Keine

---

### FR-009: Docker Deployment

**Priority:** Must Have

**Description:**
App läuft als Docker-Container mit Docker Compose. Port-Mapping 8080→8000. SQLite-Datenbank als Volume gemountet (`./data:/data`).

**Acceptance Criteria:**
- [x] `docker compose up` startet die App erfolgreich
- [x] Container Health-Check über `/health`
- [x] SQLite-DB persistiert über Container-Neustarts
- [x] Environment-Variablen über `.env` konfigurierbar
- [ ] Image-Größe < 500MB

**Dependencies:** Keine

---

### FR-010: E-Mail Notifications

**Priority:** Must Have

**Description:**
Automatische E-Mail-Benachrichtigungen via Prefect: Abo läuft ab (konfigurierbare Vorlaufzeit), Abo verlängert, Willkommens-E-Mail. SMTP-Versand.

**Acceptance Criteria:**
- [x] E-Mail bei Abo-Ablauf X Tage vorher (Standard: 7 Tage)
- [x] E-Mail bei erfolgreicher Verlängerung
- [x] Willkommens-E-Mail bei Registrierung
- [x] E-Mail-Templates in Jinja2 (HTML)
- [x] SMTP-Konfiguration über Environment-Variablen
- [x] Scheduler läuft als Prefect Flow auf CT109 (täglich 06:00 + 08:00 UTC)

**Dependencies:** FR-001, FR-004

---

### FR-011: mitKI.ai Branding

**Priority:** Must Have

**Description:**
UI im mitKI.ai Corporate Design: Navy (#0A1A3A), Orange (#F97316), Creme (#F8E3C7). Inter/Montserrat Fonts. Logo-Integration. CSS Custom Properties.

**Acceptance Criteria:**
- [x] Farben als CSS Custom Properties definiert
- [x] Tailwind CSS mit Brand-Colors erweitert
- [x] Logo SVG erstellt und über /static/logo.svg erreichbar
- [x] Konsistente Typography (Inter für Body, Montserrat für Headings)
- [x] Visuelle Konsistenz über alle Seiten

**Dependencies:** Keine

---

### FR-012: Responsive Design

**Priority:** Must Have

**Description:**
Mobile-optimierte Darstellung ab 320px Viewport. Collapsible Sidebar auf Mobile. Card-Grid passt sich an. Touch-freundliche Buttons.

**Acceptance Criteria:**
- [ ] Layout funktioniert auf 320px, 768px, 1024px, 1440px
- [x] Nav collapsed auf Mobile zu Hamburger-Menü
- [x] Tabellen scrollen horizontal auf Mobile (overflow-x-auto)
- [x] Buttons sind mindestens 44x44px (Touch-Target, min-h-[44px])
- [ ] Kein horizontaler Overflow

**Dependencies:** FR-011

---

### FR-013: Self-Service Portal

**Priority:** Should Have

**Description:**
Kunden können ihr Abo selbst verwalten: Upgrade/Downgrade, Kündigung, Profil-/Organisationsdaten ändern, Passwort ändern.

**Acceptance Criteria:**
- [ ] User kann eigenes Profil bearbeiten (Name, E-Mail, Passwort)
- [ ] User kann Abo-Plan wechseln
- [ ] User kann Abo kündigen
- [ ] Änderungen werden im Audit-Log erfasst
- [ ] Bestätigungs-Dialog vor kritischen Aktionen

**Dependencies:** FR-004, FR-005, FR-015

---

### FR-014: Admin Analytics Dashboard

**Priority:** Should Have

**Description:**
Admin-Dashboard mit: MRR (Monthly Recurring Revenue), aktive Abo-Anzahl + Trend, Churn-Rate, Top-5 Kategorien nach Kosten, Revenue-Timeline (12 Monate), Neue vs. gekündigte Abos.

**Acceptance Criteria:**
- [x] MRR-Berechnung korrekt (Summe aller monatlich normalisierten Kosten)
- [x] Churn-Rate = gekündigte / (gekündigte + aktive) im Zeitraum
- [x] MRR History als Tabelle (6 Monate, erweiterbar auf 24)
- [ ] Line-Chart: Revenue über letzte 12 Monate (Tabelle implementiert, Chart-Visualisierung offen)
- [ ] Bar-Chart: Neue vs. gekündigte Abos pro Monat
- [x] Nur für Admin-Rolle sichtbar
- [x] REST API: GET /analytics/summary + GET /analytics/mrr-history

**Dependencies:** FR-003, FR-004, FR-006

---

### FR-015: Audit Log

**Priority:** Should Have

**Description:**
Unveränderliches Log aller Änderungen: Wer (User), Wann (Timestamp), Was (Entity + Aktion), Vorher/Nachher Werte, IP-Adresse.

**Acceptance Criteria:**
- [x] Jede CRUD-Operation auf Subscriptions wird geloggt
- [x] Log enthält: User-ID, Aktion, Entity-Typ, Entity-ID, alte/neue Werte
- [x] Audit-Log ist nicht löschbar/änderbar (append-only via API)
- [x] Admin kann Audit-Log per entity_type filtern
- [x] Audit-Log Seite nur für Admins (/audit)

**Dependencies:** FR-001, FR-003

---

### FR-016: In-App Notifications

**Priority:** Should Have

**Description:**
Benachrichtigungscenter im Dashboard: Glocken-Icon mit Unread-Counter, Dropdown-Liste, Typen (Info, Warning, Success, Error), Deep-Links zu relevanten Seiten.

**Acceptance Criteria:**
- [x] Glocken-Icon in Navbar mit Unread-Badge
- [x] Dropdown zeigt letzte Notifications
- [x] Notification als gelesen markieren (einzeln + alle)
- [ ] Alle Notifications auf eigener Seite
- [x] Polling alle 30 Sekunden für neue Notifications

**Dependencies:** FR-002, FR-006

---

### FR-017: Workflow Automation

**Priority:** Should Have

**Description:**
Automatische Abo-Verlängerung wenn `auto_renew=true`: Nächstes Verlängerungsdatum wird berechnet. Automatische Statusänderung bei Ablauf. Konfigurierbare Regeln.

**Acceptance Criteria:**
- [ ] Auto-Renewal: `next_renewal` wird zum nächsten Zyklus vorgerückt
- [ ] Abgelaufene Abos werden auf Status `expired` gesetzt
- [ ] Gekündigte Abos werden bei `end_date` auf `cancelled` gesetzt
- [ ] Scheduler prüft täglich alle relevanten Abos
- [ ] Benachrichtigung bei jeder automatischen Aktion

**Dependencies:** FR-004, FR-010

---

### FR-018: Teams/Organisationen

**Priority:** Should Have

**Description:**
Mehrere User pro Tenant. Admin kann Team-Mitglieder per E-Mail einladen, Rollen zuweisen, User deaktivieren.

**Acceptance Criteria:**
- [x] Admin kann User per E-Mail einladen
- [x] Einladung mit Registrierungs-Link (7 Tage gültig, Token-basiert)
- [x] Admin kann Rollen zuweisen und ändern
- [x] Admin kann User deaktivieren (kein Login mehr)
- [x] User-Liste mit Rollen-Anzeige

**Dependencies:** FR-001, FR-002, FR-003

---

### FR-019: Tags/Kategorien

**Priority:** Should Have

**Description:**
Flexible Kategorisierung von Abonnements. Kategorien pro Tenant definierbar mit Name, Farbe, Icon. Abos können mehrere Kategorien haben (Many-to-Many).

**Acceptance Criteria:**
- [x] Kategorien erstellen mit Name und Farbe
- [x] Abo kann mehrere Kategorien haben (Many-to-Many via API)
- [x] Filter nach Kategorie in Abo-Liste (API + Web UI)
- [x] Farbige Badges in der Abo-Übersicht
- [x] Kategorie-Management Seite für Admins

**Dependencies:** FR-004

---

### FR-020: Dark Mode

**Priority:** Should Have

**Description:**
Light/Dark Theme Toggle. Dark Mode nutzt Navy als Basis. Toggle in Navbar, Persistenz via localStorage.

**Acceptance Criteria:**
- [x] Toggle-Button in Navbar
- [x] Theme-Wahl wird in localStorage gespeichert
- [x] Alle Seiten unterstützen Dark Mode
- [ ] System-Preference wird als Default verwendet
- [x] Kein Flash beim Laden (Theme wird vor Render in <head> gesetzt)

**Dependencies:** FR-011

---

### FR-021: Volltextsuche

**Priority:** Should Have

**Description:**
Suche über Abos (Name, Anbieter, Notizen) via SQLite FTS5. Suchleiste in Navbar mit Debounced-Fetch. Ergebnisse als Dropdown.

**Acceptance Criteria:**
- [ ] Suchfeld in Navbar
- [ ] Suche über Abo-Name, Anbieter, Notizen
- [ ] Ergebnisse erscheinen nach 300ms Debounce
- [ ] Suchergebnisse zeigen Abo-Name, Anbieter, Status
- [ ] Klick auf Ergebnis navigiert zum Abo

**Dependencies:** FR-004

---

### FR-022: Import/Export

**Priority:** Should Have

**Description:**
CSV-Import mit Spalten-Mapping und Vorschau. CSV-Export der gefilterten Abo-Liste. JSON-Export/Import für Vollbackup.

**Acceptance Criteria:**
- [ ] CSV-Upload mit Datei-Auswahl
- [ ] Spalten-Mapping UI (Quell-Spalte → Ziel-Feld)
- [ ] Import-Vorschau mit ersten 5 Zeilen
- [ ] CSV-Export der aktuellen Abo-Liste
- [ ] JSON-Export des gesamten Tenant-Datensatzes
- [ ] JSON-Import für Daten-Restore

**Dependencies:** FR-004

---

### FR-023: Internationalisierung (i18n)

**Priority:** Should Have

**Description:**
Mehrsprachige Oberfläche: Deutsch und Englisch. JSON-Translation-Files. Sprach-Switcher in Navbar. Locale aus User-Preference oder Accept-Language Header.

**Acceptance Criteria:**
- [ ] Alle UI-Strings in Translation-Files
- [ ] Deutsch und Englisch vollständig übersetzt
- [ ] Sprach-Switcher Dropdown in Navbar
- [ ] Sprache wird pro User gespeichert
- [ ] Fallback auf Accept-Language Header

**Dependencies:** Keine

---

### FR-024: Onboarding Wizard

**Priority:** Should Have

**Description:**
Geführte Ersteinrichtung für neue Tenants: Schritt 1 = Organisationsname + Währung, Schritt 2 = Team-Mitglied einladen, Schritt 3 = Erstes Abo anlegen.

**Acceptance Criteria:**
- [ ] 3-Step Wizard nach erstem Login
- [ ] Step 1: Tenant-Name, Standard-Währung, Locale
- [ ] Step 2: Optional Team-Mitglied einladen
- [ ] Step 3: Erstes Abo anlegen (mit Vorlage)
- [ ] Wizard kann übersprungen werden
- [ ] Wizard erscheint nur einmal

**Dependencies:** FR-001, FR-018, FR-004

---

### FR-025: Multi-Currency

**Priority:** Should Have

**Description:**
Abos können in verschiedenen Währungen erfasst werden (EUR, USD, CHF etc.). Währungssymbol wird korrekt angezeigt. Tenant hat Standard-Währung.

**Acceptance Criteria:**
- [ ] Währung pro Abo auswählbar
- [ ] Währungssymbole korrekt dargestellt (€, $, CHF)
- [ ] Tenant hat konfigurierbare Standard-Währung
- [ ] Dashboard zeigt Kosten gruppiert nach Währung
- [ ] Import/Export berücksichtigt Währungen

**Dependencies:** FR-004

---

### FR-026: Outgoing Webhooks

**Priority:** Could Have

**Description:**
Tenants registrieren Webhook-URLs für Events: `subscription.created`, `subscription.updated`, `subscription.cancelled`, `subscription.renewed`. HMAC-SHA256 Signatur.

**Acceptance Criteria:**
- [x] Webhook-Endpoint registrieren mit URL + Events
- [x] HMAC-SHA256 Signatur im `X-Webhook-Signature` Header
- [ ] Retry-Logic: 3 Versuche mit Exponential Backoff *(offen)*
- [ ] Delivery-Log mit Status-Codes *(offen)*
- [ ] Test-Button zum manuellen Auslösen *(offen)*

**Dependencies:** FR-004, FR-007

---

### FR-027: Coupons/Rabattcodes

**Priority:** Could Have

**Description:**
Rabattcode-System: Codes mit prozentualen oder festen Rabatten, Gültigkeitszeitraum, maximale Nutzungsanzahl.

**Acceptance Criteria:**
- [ ] Coupon erstellen mit Code, Typ (Prozent/Fix), Wert
- [ ] Gültigkeitszeitraum (von/bis)
- [ ] Maximale Nutzungsanzahl
- [ ] Coupon auf Abo anwenden, Kosten anpassen
- [ ] Nutzungszähler wird automatisch erhöht

**Dependencies:** FR-004

---

### FR-028: SSO Integration

**Priority:** Could Have

**Description:**
Login via Google OAuth2 und Microsoft Azure AD (OIDC). Account-Erstellung oder -Verknüpfung. Tenant-Admin aktiviert/deaktiviert SSO-Provider.

**Acceptance Criteria:**
- [x] "Login mit Google" Button auf Login-Seite (GET /api/v1/auth/sso/google)
- [x] "Login mit Microsoft" Button auf Login-Seite
- [x] Neuer Account wird automatisch erstellt bei erstem SSO-Login
- [x] Bestehender Account mit gleichem E-Mail wird verknüpft
- [ ] SSO pro Tenant aktivierbar/deaktivierbar *(offen — aktuell global via Settings)*

**Dependencies:** FR-002, FR-031

---

### FR-029: GraphQL API

**Priority:** Could Have

**Description:**
GraphQL API neben REST via Strawberry-GraphQL. Queries für alle Entitäten. Mutations für CRUD. Playground unter `/graphql`.

**Acceptance Criteria:**
- [x] GraphQL Endpoint unter `/graphql`
- [x] Queries: subscriptions, subscription(id), plans
- [x] Mutations: createSubscription, deleteSubscription
- [x] Authentication über selben Mechanismus wie REST (Bearer + Session)
- [x] GraphQL Playground (GraphiQL) erreichbar
- [ ] Queries für categories, users *(noch offen)*

**Dependencies:** FR-007, FR-031

---

### FR-030: Custom Fields

**Priority:** Could Have

**Description:**
Tenant-Admins definieren eigene Felder (Text, Number, Date, Select) pro Abo. Felder werden dynamisch in Formularen gerendert. Werte in JSON gespeichert.

**Acceptance Criteria:**
- [ ] Custom Field Definition: Name, Typ, Optionen (bei Select)
- [ ] Felder erscheinen im Abo-Formular
- [ ] Werte werden in `custom_fields_json` gespeichert
- [ ] Custom Fields in Abo-Detailansicht sichtbar
- [ ] Custom Fields im Export enthalten

**Dependencies:** FR-004

---

### FR-031: OAuth2/JWT Auth Upgrade

**Priority:** Could Have

**Description:**
Upgrade von HTTP Basic Auth auf JWT: Access Token + Refresh Token. Web-UI nutzt Session-Cookie, API nutzt Bearer Token.

**Acceptance Criteria:**
- [x] `POST /api/v1/auth/token` gibt JWT zurück (OAuth2 Password Flow)
- [ ] `POST /api/v1/auth/refresh` erneuert Token *(offen)*
- [x] Web-UI Session via Cookie (user_id-basiert, kompatibel)
- [x] API-Clients nutzen Bearer Token im Authorization Header
- [x] Bestehende Auth-Dependencies unterstützen beide Methoden (Bearer + Session)

**Dependencies:** FR-002

---

### FR-032: Strukturiertes Logging (Loki/Grafana)

**Priority:** Could Have

**Description:**
JSON-Line Logging mit Request-ID Correlation. Kompatibel mit Loki-Collection. Request-ID Middleware generiert UUID pro Request.

**Acceptance Criteria:**
- [x] Alle Logs als JSON in Prod (structlog, `is_production=true`)
- [x] Request-ID in jedem Log-Eintrag (X-Request-ID Header + Context)
- [ ] Log-Level konfigurierbar via ENV *(offen — aktuell hardcoded INFO)*
- [ ] Loki kann Logs scrapen *(Infra-Konfiguration offen)*
- [ ] Grafana Dashboard Template *(offen)*

**Dependencies:** FR-008

---

### FR-033: YouTube Showcase

**Priority:** Could Have

**Description:**
Demo-Daten für ansprechende Präsentation. Landing Page (unauthenticated) mit Feature-Highlights. Seed-Script für Showcase-Daten.

**Acceptance Criteria:**
- [x] Seed-Script erstellt Demo-Daten (1 Tenant, 10 Subs, 3 Plans)
- [x] Landing Page mit Feature-Übersicht und YouTube-Placeholder
- [ ] Demo-Tenant mit realistisch vorbefüllten Daten (>30 Subs, mehrere Teams) *(offen)*
- [ ] Visuell ansprechendes Dashboard für Video-Aufnahmen *(seed-Verbesserung offen)*

**Dependencies:** FR-006, FR-011

---

### FR-034: Staging Environment

**Priority:** Could Have

**Description:**
Separate Staging-Umgebung auf Coolify: eigene App, eigener Branch (`staging`), eigener Port (8081), eigene Datenbank.

**Acceptance Criteria:**
- [ ] Coolify App "SubManager-Staging" konfiguriert
- [ ] Auto-Deploy bei Push auf `staging` Branch
- [ ] Eigenes Volume für Staging-Datenbank
- [ ] Eigene Environment-Variablen
- [ ] Erreichbar unter separater URL

**Dependencies:** FR-009

---

### FR-035: DB Migration Path

**Priority:** Could Have

**Description:**
Code so geschrieben, dass SQLite → PostgreSQL Wechsel mit minimalem Aufwand möglich. Alembic für Migrations. Kein Raw SQL außer FTS5.

**Acceptance Criteria:**
- [x] Alle DB-Zugriffe über SQLAlchemy ORM
- [x] Alembic Migrations mit `render_as_batch=True` (SQLite-kompatibel)
- [x] UUIDs als TEXT (kompatibel mit beiden DBs)
- [x] FTS5-Code isoliert in `search_service.py`
- [ ] CI kann Tests gegen PostgreSQL laufen lassen *(offen)*

**Dependencies:** FR-004

---

### FR-036: Icon Bibliothek

**Priority:** Should Have

**Description:**
Visuelle Icon-Bibliothek für Abonnements und Kategorien. Nutzer können beim Erstellen/Bearbeiten eines Abos ein passendes Icon auswählen (z.B. GitHub-Logo, AWS-Icon, Slack-Icon). Icons werden zentral gepflegt und per Suche/Tags gefiltert.

**Acceptance Criteria:**
- [ ] Icon-Bibliothek mit mindestens 50 gängigen SaaS/Tool-Icons
- [ ] Icon-Picker im Abo-Formular (Suche + Grid-Ansicht)
- [ ] Icons werden in Abo-Liste und Dashboard angezeigt
- [ ] Icons sind SVG oder hochauflösendes PNG
- [ ] Admin kann neue Icons hinzufügen
- [ ] Icons haben Tags zur Kategorisierung (z.B. "SaaS", "Cloud", "Dev")

**Dependencies:** FR-004, FR-019

---

### FR-037: NocoDB Integration (Icon-Verwaltung)

**Priority:** Could Have

**Description:**
Anbindung an NocoDB (Container 106, nocodb.mitki.ai) als Backend für die Icon-Bibliothek. Icons werden in NocoDB gepflegt (Name, SVG/URL, Tags, Kategorie) und vom Subscription Manager per REST API abgerufen und lokal gecached.

**Acceptance Criteria:**
- [ ] NocoDB-Tabelle "Icons" mit Spalten: Name, URL, Tags, Category, Preview
- [ ] REST API Abruf der Icons aus NocoDB
- [ ] Lokaler Cache (In-Memory oder File) mit TTL
- [ ] Fallback auf Emoji-Icons wenn NocoDB nicht erreichbar

**Dependencies:** FR-036

---

## Non-Functional Requirements

Non-Functional Requirements (NFRs) define **how** the system performs - quality attributes and constraints.

---

### NFR-001: API Response Time

**Priority:** Must Have

**Description:**
REST API Antwortzeit unter 500ms für 95% aller Requests unter normaler Last.

**Acceptance Criteria:**
- [ ] p95 Latency < 500ms gemessen über 1000 Requests
- [ ] Keine Endpoints mit durchschnittlicher Latency > 1s

**Rationale:**
Nutzer erwarten schnelle Interaktion. Slow APIs führen zu schlechter UX und höherer Absprungrate.

---

### NFR-002: Dashboard Load Time

**Priority:** Must Have

**Description:**
Das Dashboard (inkl. Charts und KPIs) lädt vollständig in unter 2 Sekunden.

**Acceptance Criteria:**
- [ ] Time to First Meaningful Paint < 1s
- [ ] Alle Charts gerendert < 2s
- [ ] Getestet mit 100 Abos pro Tenant

**Rationale:**
Dashboard ist die meistgenutzte Seite. Langsame Ladezeiten reduzieren die tägliche Nutzung.

---

### NFR-003: Uptime

**Priority:** Must Have

**Description:**
System-Verfügbarkeit von mindestens 99% (≈ 7.3 Stunden Downtime/Monat erlaubt). Gemessen über Coolify Health-Check.

**Acceptance Criteria:**
- [ ] Health-Check alle 30 Sekunden
- [ ] Auto-Restart bei Container-Crash (Docker restart policy)
- [ ] Monatliches Uptime-Tracking

**Rationale:**
Als SaaS-Produkt muss die Verfügbarkeit zuverlässig sein, aber 99.9% wäre für den Start zu aufwändig.

---

### NFR-004: Password Storage

**Priority:** Must Have

**Description:**
Alle Passwörter mit bcrypt gehasht. Minimum Cost Factor 12.

**Acceptance Criteria:**
- [ ] Passwörter niemals im Klartext gespeichert
- [ ] bcrypt mit Cost Factor ≥ 12
- [ ] Passwort-Hashing in dedizierter Security-Funktion

**Rationale:**
Grundlegende Sicherheitsanforderung für jede Anwendung mit User-Accounts.

---

### NFR-005: Session Security

**Priority:** Must Have

**Description:**
Session-Cookies mit HTTP-Only, Secure und SameSite Flags.

**Acceptance Criteria:**
- [ ] Cookie: `HttpOnly=true`
- [ ] Cookie: `Secure=true` (in Production)
- [ ] Cookie: `SameSite=Lax`
- [ ] Cookie-Inhalt ist signiert/verschlüsselt

**Rationale:**
Schutz vor XSS und CSRF Angriffen.

---

### NFR-006: Tenant Data Isolation

**Priority:** Must Have

**Description:**
Absolute Datenisolation zwischen Tenants. Kein Cross-Tenant Zugriff auf Daten möglich.

**Acceptance Criteria:**
- [ ] Jede DB-Query filtert nach `tenant_id`
- [ ] API-Tests bestätigen: User A kann User B's Daten nicht abrufen
- [ ] Automatisierte Tests für Tenant-Isolation vorhanden

**Rationale:**
Multi-Tenant SaaS erfordert strikte Datentrennung. Datenlecks wären geschäftskritisch.

---

### NFR-007: Browser Support

**Priority:** Should Have

**Description:**
Unterstützung der letzten 2 Versionen von Chrome, Firefox, Safari und Edge.

**Acceptance Criteria:**
- [ ] Keine JavaScript-Fehler in unterstützten Browsern
- [ ] Layout korrekt in allen Browsern
- [ ] Keine Nutzung von experimentellen Web-APIs

**Rationale:**
Breite Browser-Kompatibilität sichert Zugänglichkeit für alle Kunden.

---

### NFR-008: Mobile Breakpoints

**Priority:** Should Have

**Description:**
Responsive Design ab 320px Viewport-Breite. Breakpoints: 320px (Mobile), 768px (Tablet), 1024px (Desktop), 1440px (Wide).

**Acceptance Criteria:**
- [ ] Keine UI-Elemente abgeschnitten bei 320px
- [ ] Touch-Targets mindestens 44x44px
- [ ] Tailwind responsive Classes korrekt verwendet

**Rationale:**
Mobile Nutzung ist Standard. Kunden verwalten Abos auch unterwegs.

---

### NFR-009: Test Coverage

**Priority:** Should Have

**Description:**
Mindestens 70% Code Coverage mit pytest. Coverage-Report in CI sichtbar.

**Acceptance Criteria:**
- [x] `pytest --cov=app` zeigt ≥ 70% Coverage — **aktuell 89%** (247 Tests)
- [ ] Coverage-Report im CI-Output *(CI-Integration offen)*
- [x] Kritische Pfade (Auth, Tenant-Isolation, CRUD) bei 90%+

**Rationale:**
Automatisierte Tests sichern Qualität bei schneller Entwicklung und Refactoring.

---

### NFR-010: Code Quality

**Priority:** Must Have

**Description:**
Ruff Linting und mypy Type-Checking als Pflicht in CI. Kein Merge bei Fehlern.

**Acceptance Criteria:**
- [ ] `ruff check app/ tests/` ohne Fehler
- [ ] `mypy app/` ohne Fehler (mit `--ignore-missing-imports`)
- [ ] CI blockiert Merge bei Lint/Type Fehlern

**Rationale:**
Konsistente Code-Qualität von Anfang an verhindert technische Schulden.

---

### NFR-011: Concurrent Users

**Priority:** Should Have

**Description:**
System unterstützt 50 gleichzeitige Nutzer pro Instanz ohne Performanceverlust.

**Acceptance Criteria:**
- [ ] 50 parallele Requests ohne HTTP 5xx Fehler
- [ ] Response-Zeiten bleiben unter NFR-001 Grenzwert
- [ ] SQLite WAL-Mode aktiviert für bessere Concurrency

**Rationale:**
Für den Start ausreichend. Bei Wachstum: Migration auf PostgreSQL.

---

### NFR-012: API Standard

**Priority:** Must Have

**Description:**
REST API konform mit OpenAPI 3.0 Spezifikation. Auto-generiert durch FastAPI.

**Acceptance Criteria:**
- [ ] OpenAPI 3.0 Schema unter `/openapi.json`
- [ ] Swagger UI unter `/docs`
- [ ] ReDoc unter `/redoc`
- [ ] Schema validiert gegen OpenAPI 3.0 Spec

**Rationale:**
Standard-konforme API erleichtert Integration für Drittanbieter.

---

## Epics

Epics are logical groupings of related functionality that will be broken down into user stories during sprint planning (Phase 4).

Each epic maps to multiple functional requirements and will generate 2-10 stories.

---

### EPIC-001: Core Platform & Authentication

**Description:**
Grundlegende Plattform aufsetzen: Multi-Tenant Architektur, User-Authentication, RBAC, Docker-Deployment, Health-Endpoints und mitKI.ai Branding.

**Functional Requirements:**
- FR-001: Multi-Tenant Isolation
- FR-002: User Authentication
- FR-003: RBAC
- FR-008: Health/Metrics Endpoints
- FR-009: Docker Deployment
- FR-011: mitKI.ai Branding

**Story Count Estimate:** 8-10

**Priority:** Must Have

**Business Value:**
Ohne diese Basis kann kein anderes Feature existieren. Dies ist das Fundament der gesamten Plattform.

---

### EPIC-002: Subscription Management

**Description:**
Kern-Funktionalität: Abos und Pläne verwalten, Dashboard mit KPIs und Charts, responsive Darstellung, Kategorien und Multi-Currency.

**Functional Requirements:**
- FR-004: Subscription CRUD
- FR-005: Plan Management
- FR-006: Web Dashboard
- FR-012: Responsive Design
- FR-019: Tags/Kategorien
- FR-025: Multi-Currency

**Story Count Estimate:** 8-10

**Priority:** Must Have

**Business Value:**
Die Kern-Wertschöpfung des Produkts. Kunden nutzen die App primär für Abo-Verwaltung und Kosten-Überblick.

---

### EPIC-003: Notifications & Automation

**Description:**
E-Mail Benachrichtigungen, In-App Notifications und Workflow-Automation (Auto-Renewal, Auto-Expiry).

**Functional Requirements:**
- FR-010: E-Mail Notifications
- FR-016: In-App Notifications
- FR-017: Workflow Automation

**Story Count Estimate:** 5-7

**Priority:** Must Have

**Business Value:**
Automatisierung reduziert manuellen Aufwand. Notifications halten Nutzer informiert und fördern Engagement.

---

### EPIC-004: Self-Service & Teams

**Description:**
Kunden-Self-Service Portal, Team-Management mit Einladungen, und Onboarding Wizard für neue Tenants.

**Functional Requirements:**
- FR-013: Self-Service Portal
- FR-018: Teams/Organisationen
- FR-024: Onboarding Wizard

**Story Count Estimate:** 6-8

**Priority:** Should Have

**Business Value:**
Self-Service reduziert Support-Aufwand. Teams ermöglichen B2B-Nutzung. Onboarding senkt die Einstiegshürde.

---

### EPIC-005: Search, i18n & Data Management

**Description:**
Volltextsuche, Mehrsprachigkeit (DE+EN), und Daten Import/Export (CSV/JSON).

**Functional Requirements:**
- FR-021: Volltextsuche
- FR-022: Import/Export
- FR-023: Internationalisierung (i18n)

**Story Count Estimate:** 5-7

**Priority:** Should Have

**Business Value:**
i18n öffnet den englischsprachigen Markt. Import/Export erleichtert Onboarding. Suche verbessert UX bei wachsendem Datenbestand.

---

### EPIC-006: Admin Dashboard & Quality

**Description:**
Admin Analytics mit Umsatz/Churn/Trends, Audit Log, Dark Mode, und Public REST API Erweiterungen.

**Functional Requirements:**
- FR-007: Public REST API
- FR-014: Admin Analytics Dashboard
- FR-015: Audit Log
- FR-020: Dark Mode

**Story Count Estimate:** 6-8

**Priority:** Should Have

**Business Value:**
Analytics ermöglicht datengetriebene Entscheidungen. Audit Log schafft Vertrauen. Dark Mode ist Standard-Erwartung.

---

### EPIC-007: Integrations

**Description:**
Outgoing Webhooks, Coupon/Rabattcode-System, und tenant-spezifische Custom Fields.

**Functional Requirements:**
- FR-026: Outgoing Webhooks
- FR-027: Coupons/Rabattcodes
- FR-030: Custom Fields

**Story Count Estimate:** 5-7

**Priority:** Could Have

**Business Value:**
Webhooks ermöglichen Drittanbieter-Integration. Coupons fördern Wachstum. Custom Fields machen die App flexibler.

---

### EPIC-008: Security Upgrade

**Description:**
Upgrade auf OAuth2/JWT Authentication, SSO (Google/Microsoft), und GraphQL API neben REST.

**Functional Requirements:**
- FR-028: SSO Integration
- FR-029: GraphQL API
- FR-031: OAuth2/JWT Auth Upgrade

**Story Count Estimate:** 5-7

**Priority:** Could Have

**Business Value:**
Enterprise-Kunden erwarten SSO. JWT ermöglicht sichere API-Nutzung. GraphQL ist ein Differenzierungsmerkmal.

---

### EPIC-009: Production Readiness & Launch

**Description:**
Strukturiertes Logging mit Loki/Grafana, YouTube Showcase-Vorbereitung, Staging Environment, und PostgreSQL Migration Path.

**Functional Requirements:**
- FR-032: Strukturiertes Logging
- FR-033: YouTube Showcase
- FR-034: Staging Environment
- FR-035: DB Migration Path

**Story Count Estimate:** 4-6

**Priority:** Could Have

**Business Value:**
Professionelle Ops-Infrastruktur für nachhaltigen Betrieb. Showcase generiert Marketing-Content und Community-Interesse.

---

## User Stories (High-Level)

User stories follow the format: "As a [user type], I want [goal] so that [benefit]."

---

### EPIC-001: Core Platform & Authentication

- Als **neuer Kunde** möchte ich **mich registrieren und einen Tenant erstellen**, damit ich **die Plattform für meine Organisation nutzen kann**.
- Als **Admin** möchte ich **neue Team-Mitglieder mit spezifischen Rollen einladen**, damit ich **den Zugriff auf unsere Daten kontrollieren kann**.
- Als **DevOps** möchte ich **den Container mit `docker compose up` starten**, damit ich **die App schnell deployen kann**.

### EPIC-002: Subscription Management

- Als **User** möchte ich **ein neues Abo mit allen Details erfassen**, damit ich **einen Überblick über meine laufenden Kosten habe**.
- Als **User** möchte ich **auf dem Dashboard meine monatlichen Gesamtkosten und anstehende Verlängerungen sehen**, damit ich **rechtzeitig reagieren kann**.
- Als **Admin** möchte ich **Abo-Pläne als Vorlagen definieren**, damit mein **Team Abos konsistent erfassen kann**.

### EPIC-003: Notifications & Automation

- Als **User** möchte ich **7 Tage vor Abo-Ablauf eine E-Mail erhalten**, damit ich **entscheiden kann ob ich verlängere oder kündige**.
- Als **User** möchte ich **In-App Benachrichtigungen über Abo-Änderungen sehen**, damit ich **auch ohne E-Mail informiert bin**.
- Als **Admin** möchte ich **Auto-Renewal Regeln konfigurieren**, damit **Abos automatisch verlängert werden**.

### EPIC-004: Self-Service & Teams

- Als **Kunde** möchte ich **mein Abo selbst upgraden oder kündigen**, damit ich **nicht auf den Support warten muss**.
- Als **neuer Tenant** möchte ich **durch einen Wizard geführt werden**, damit ich **schnell starten kann**.
- Als **Admin** möchte ich **Team-Mitglieder einladen und deren Rollen verwalten**, damit **jeder die richtigen Berechtigungen hat**.

### EPIC-005: Search, i18n & Data Management

- Als **User** möchte ich **über eine Suchleiste schnell ein bestimmtes Abo finden**, damit ich **nicht durch lange Listen scrollen muss**.
- Als **User** möchte ich **die App auf Deutsch oder Englisch nutzen**, damit ich **in meiner bevorzugten Sprache arbeite**.
- Als **Admin** möchte ich **alle Abos als CSV exportieren**, damit ich **die Daten in Excel analysieren kann**.

### EPIC-006: Admin Dashboard & Quality

- Als **Admin** möchte ich **MRR, Churn-Rate und Abo-Trends sehen**, damit ich **datenbasierte Geschäftsentscheidungen treffen kann**.
- Als **Admin** möchte ich **nachvollziehen können wer wann was geändert hat**, damit ich **Compliance-Anforderungen erfülle**.
- Als **User** möchte ich **zwischen Light und Dark Mode wechseln**, damit ich **bei unterschiedlichen Lichtverhältnissen komfortabel arbeite**.

### EPIC-007: Integrations

- Als **Admin** möchte ich **Webhook-URLs registrieren**, damit **externe Systeme bei Abo-Änderungen benachrichtigt werden**.
- Als **Admin** möchte ich **Rabattcodes erstellen und auf Abos anwenden**, damit ich **Promotions durchführen kann**.
- Als **Admin** möchte ich **eigene Felder pro Abo definieren**, damit ich **branchenspezifische Daten erfassen kann**.

### EPIC-008: Security Upgrade

- Als **Enterprise-Kunde** möchte ich **mich mit meinem Google/Microsoft Account anmelden**, damit ich **kein separates Passwort brauche**.
- Als **Entwickler** möchte ich **die API über GraphQL abfragen**, damit ich **nur die Daten bekomme die ich brauche**.

### EPIC-009: Production Readiness & Launch

- Als **DevOps** möchte ich **strukturierte Logs in Grafana sehen**, damit ich **Probleme schnell diagnostizieren kann**.
- Als **mitKI.ai** möchte ich **eine Demo-Instanz mit realistischen Daten**, damit ich **ein ansprechendes YouTube-Video erstellen kann**.

---

## User Personas

### Persona 1: Geschäftsführer (50+)
- **Rolle:** Entscheidungsträger, wenig technisch
- **Bedürfnis:** Kostenüberblick, einfache Bedienung, deutsche Oberfläche
- **Nutzung:** Dashboard, Reports, gelegentliche Abo-Verwaltung
- **Pain Point:** Unübersichtliche Excel-Listen für Abo-Tracking

### Persona 2: IT-Leiter
- **Rolle:** Technisch versiert, verwaltet SaaS-Tools für die Organisation
- **Bedürfnis:** Zentrales Management, Team-Zugriff, API-Integration
- **Nutzung:** Abo-CRUD, Team-Management, Webhooks, API
- **Pain Point:** Verstreute Abo-Informationen über verschiedene Abteilungen

### Persona 3: Solopreneur
- **Rolle:** Einzelunternehmer, selbst technisch aktiv
- **Bedürfnis:** Schneller Start, Self-Service, Export für Buchhaltung
- **Nutzung:** Abo-Tracking, CSV-Export, E-Mail-Reminders
- **Pain Point:** Vergessene Abo-Verlängerungen und überraschende Kosten

---

## User Flows

### Flow 1: Erstregistrierung → Onboarding → Erstes Abo
1. Landing Page → "Registrieren" klicken
2. E-Mail + Passwort eingeben → Account erstellt
3. Onboarding Wizard: Organisationsname + Währung
4. Optional: Team-Mitglied einladen
5. Erstes Abo erfassen → Dashboard zeigt Übersicht

### Flow 2: Tägliche Nutzung → Dashboard → Abo verwalten
1. Login → Dashboard öffnet sich
2. KPIs prüfen (Kosten, Verlängerungen)
3. Notification-Badge zeigt 2 ungelesene Nachrichten
4. Klick auf Notification → "Abo XY läuft in 3 Tagen ab"
5. Klick → Abo-Detail → Verlängern oder Kündigen

### Flow 3: Admin → Analytics → Export
1. Login als Admin → Admin-Dashboard
2. MRR und Churn-Rate prüfen
3. Abo-Liste filtern nach Kategorie "SaaS"
4. CSV-Export für Buchhaltung

---

## Dependencies

### Internal Dependencies

- **branding.md:** Design-Tokens, Farben, Fonts für UI-Implementierung
- **Proxmox Server:** Hosting-Infrastruktur muss laufen
- **Coolify:** PaaS muss konfiguriert sein
- **GitHub Repository:** Muss erstellt werden

### External Dependencies

- **SMTP Server:** Für E-Mail-Versand (konfigurierbar)
- **Google OAuth2 API:** Für SSO (Phase 4)
- **Microsoft Azure AD:** Für SSO (Phase 4)
- **Tailwind CSS CDN:** Für Styling
- **Chart.js CDN:** Für Dashboard-Charts
- **Strawberry-GraphQL:** Für GraphQL API (Phase 4)

---

## Assumptions

1. Proxmox Server ist verfügbar und hat ausreichend Ressourcen für Staging + Production
2. Coolify ist korrekt installiert und kann GitHub-Repos verbinden
3. SQLite reicht für die initiale Nutzerlast (< 50 concurrent users)
4. SMTP-Server ist vorhanden oder wird bereitgestellt
5. Kein Payment-Processing nötig — Abrechnung erfolgt extern
6. Domain/Subdomain für die App ist verfügbar
7. GitHub Repository wird unter mitKI.ai Organisation erstellt

---

## Out of Scope

Die folgenden Features wurden bewusst ausgeschlossen:

- **Payment Processing** — Keine Stripe/PayPal Integration
- **Rate Limiting** — Nicht für MVP nötig
- **DB Backup System** — Kein eingebautes Backup
- **Kalender-Integration** — Kein Google Calendar Sync
- **Activity Feed** — Kein chronologischer Feed
- **Public Status Page** — Keine öffentliche Status-Seite
- **PDF Export** — Kein PDF-Report-Generator
- **Plugin/Marketplace System** — Monolithische Architektur
- **Trial Periods** — Keine kostenlosen Testzeiträume
- **API Key Management** — Keine Self-Service API-Keys für Kunden *(für Sprint 10 vorgeschlagen)*
- **DSGVO Compliance** — Keine eingebauten Datenschutz-Features
- **Native Mobile App** — Nur responsive Web
- **Offline-Funktionalität** — Nur Online-Nutzung

---

## Open Questions

1. **Domain:** Unter welcher Domain/Subdomain wird die App erreichbar sein?
2. **SMTP:** Welcher SMTP-Server wird verwendet? (Eigener, SendGrid, Mailgun?)
3. **GitHub Org:** Wird das Repo unter `mitki-ai/` oder einem persönlichen Account erstellt?
4. **Coolify Version:** Welche Coolify-Version läuft? (Relevant für Konfiguration)
5. **SSL/TLS:** Wird Coolify SSL-Zertifikate automatisch verwalten (Let's Encrypt)?

---

## Approval & Sign-off

### Stakeholders

| Rolle | Name | Verantwortung |
|-------|------|---------------|
| Product Owner | Eddy | Feature-Priorisierung, Abnahme |
| Engineering Lead | Eddy + Claude Code | Technische Umsetzung |
| Design Lead | mitKI.ai Branding | Visual Design (branding.md) |

### Approval Status

- [ ] Product Owner
- [ ] Engineering Lead
- [ ] Design Lead
- [ ] QA Lead

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-27 | Eddy | Initial PRD basierend auf 50 Vision-Fragen |
| 2.0 | 2026-03-30 | Eddy + Claude Code | Implementation Status Update: alle 9 Sprints / 230 Points abgeschlossen. Acceptance Criteria auf tatsächlichen Stand aktualisiert. 5 neue Story-Vorschläge hinzugefügt. |

---

## Next Steps

### Phase 3: Architecture

Run `/bmad:architecture` to create system architecture based on these requirements.

The architecture will address:
- All functional requirements (FRs)
- All non-functional requirements (NFRs)
- Technical stack decisions
- Data models and APIs
- System components

### Phase 4: Sprint Planning

After architecture is complete, run `/bmad:sprint-planning` to:
- Break epics into detailed user stories
- Estimate story complexity
- Plan sprint iterations
- Begin implementation

---

**This document was created using BMAD Method v6 - Phase 2 (Planning)**

*Updated 2026-03-30 — Implementation complete. See Sprint 10 proposals below.*

---

## Sprint 10 — Vorgeschlagene User Stories

> Basierend auf dem vollständigen Durchlauf aller 9 Sprints und dem aktuellen Stand der App.
> Diese 5 Stories wurden sorgfältig ausgewählt, weil sie (a) echten Nutzer-Mehrwert liefern,
> (b) auf vorhandener Infrastruktur aufbauen, und (c) die häufigsten Schwachstellen adressieren.

---

### STORY-049: Budget Alerts & Ausgaben-Limits

**Epic:** EPIC-002 (Subscription Management)
**Priority:** Should Have
**Aufwand:** 5 Points

**User Story:**
Als **Admin** möchte ich **ein monatliches Budget-Limit pro Kategorie oder gesamt setzen**,
damit ich **frühzeitig gewarnt werde, bevor mein Team das SaaS-Budget überschreitet**.

**Warum diese Story?**
Das ist der häufigste Grund, warum Geschäftsführer ein Abo-Tracking-Tool überhaupt kaufen.
MRR *sehen* ist gut — aber automatisch *gewarnt werden*, wenn man auf dem Weg ist das Budget
zu überschreiten, ist der eigentliche Mehrwert. Aktuell fehlt diese Feedback-Schleife komplett.

**Acceptance Criteria:**
- [ ] Admin kann ein monatliches Budget (€) pro Kategorie oder als Gesamt-Limit setzen
- [ ] Wenn aktueller MRR 80% des Budgets erreicht → In-App Notification + E-Mail (Warning)
- [ ] Wenn Budget überschritten → In-App Notification + E-Mail (Alert)
- [ ] Dashboard zeigt Budget-Fortschrittsbalken (z.B. "€ 1.240 / € 1.500")
- [ ] Budget-Check läuft täglich als Prefect Flow (nutzt bestehenden renewal-reminder Flow)
- [ ] Budget-Einstellungen auf der Settings-Seite konfigurierbar
- [ ] Tenant-isoliert (jedes Budget nur für eigenen Tenant sichtbar)

**Technical Notes:**
Neues Modell `BudgetAlert` (tenant_id, category_id nullable, monthly_limit, warn_at_percent=80).
Prefect Flow ruft `GET /internal/check-budgets` auf. Nutzt bestehenden `EmailService` + `NotificationService`.

**Dependencies:** FR-014 (Analytics), FR-010 (E-Mail), FR-016 (Notifications)

---

### STORY-050: API Key Management

**Epic:** EPIC-008 (Security Upgrade)
**Priority:** Should Have
**Aufwand:** 5 Points

**User Story:**
Als **IT-Leiter** möchte ich **benannte, widerrufliche API-Keys erstellen**,
damit ich **Integrationen (n8n, Zapier, eigene Skripte) dauerhaft authentifizieren kann,
ohne mein Passwort zu teilen oder JWT-Token manuell zu erneuern**.

**Warum diese Story?**
JWT-Bearer-Tokens laufen nach 60 Minuten ab — für automatisierte Integrationen unbrauchbar.
Aktuell steht "API Key Management" bewusst in der Out-of-Scope-Liste, aber der Wunsch wurde
beim Aufbau der Webhooks + GraphQL API deutlich: Wer diese nutzen will, braucht permanente Keys.
Das ist der Unterschied zwischen "ich kann es konfigurieren" und "es läuft zuverlässig".

**Acceptance Criteria:**
- [ ] Admin kann benannte API-Keys erstellen ("n8n Integration", "Backup Script")
- [ ] Key-Wert wird genau einmal bei Erstellung angezeigt (danach nie mehr, Stripe-Stil)
- [ ] Keys können einzeln widerrufen werden (sofort wirksam)
- [ ] Letztes-Verwendung-Datum wird pro Key getrackt
- [ ] API-Key im `Authorization: ApiKey <key>` Header oder `X-API-Key` Header akzeptiert
- [ ] `get_current_user` Dependency prüft API-Keys als dritten Auth-Mechanismus (nach Bearer + Session)
- [ ] Maximale 10 Keys pro Tenant

**Technical Notes:**
Neues Modell `APIKey` (id, tenant_id, user_id, name, key_hash, last_used_at, created_at, revoked_at).
Key wird als `sha256(random_bytes(32))` gespeichert — niemals Klartext in DB.
`app/dependencies.py` erweitert um dritte Prüfung.

**Dependencies:** FR-031 (JWT), FR-007 (REST API)

---

### STORY-051: Subscription Cost Change History

**Epic:** EPIC-002 (Subscription Management)
**Priority:** Could Have
**Aufwand:** 3 Points

**User Story:**
Als **Admin** möchte ich **sehen, wann und wie sich der Preis eines Abonnements geändert hat**,
damit ich **die Kostensteigerung über Zeit dokumentieren und begründen kann**.

**Warum diese Story?**
SaaS-Preise steigen regelmäßig. "Wann hat Slack den Preis erhöht?" ist eine echte Frage,
die aktuell nicht beantwortet werden kann, weil der `cost`-Wert einfach überschrieben wird.
Der Audit-Log erfasst das technisch zwar (`old_values`), aber nicht strukturiert auswertbar.
Mit einer dedizierten Cost History bekommt jedes Abo einen nützlichen "Timeline"-Reiter.

**Acceptance Criteria:**
- [ ] Wenn `cost` eines Abos geändert wird, wird automatisch ein `SubscriptionCostHistory` Eintrag erstellt
- [ ] Eintrag enthält: subscription_id, old_cost, new_cost, changed_by_id, changed_at
- [ ] Abo-Detailseite zeigt Preisentwicklung als kompakte Timeline
- [ ] API: `GET /subscriptions/{id}/cost-history` gibt die History zurück
- [ ] Tenant-isoliert und nur für Admins + User der eigenen Subscription sichtbar
- [ ] Chart.js Mini-Line-Chart in der Detailansicht (nutzt vorhandene Chart.js-Einbindung)

**Technical Notes:**
Neues Modell `SubscriptionCostHistory`. Hook in `SubscriptionService.update()`:
wenn `cost` im kwargs vorhanden und anders als aktuell → History-Eintrag anlegen.
Kein Breaking Change am bestehenden API.

**Dependencies:** FR-004 (Subscription CRUD), FR-015 (Audit Log)

---

### STORY-052: Duplicate Subscription Detection

**Epic:** EPIC-002 (Subscription Management)
**Priority:** Could Have
**Aufwand:** 3 Points

**User Story:**
Als **User** möchte ich **beim Erstellen eines neuen Abos gewarnt werden, wenn es bereits ein ähnliches gibt**,
damit ich **verhindere, dass dasselbe Tool doppelt erfasst und bezahlt wird**.

**Warum diese Story?**
Doppelt bezahlte Abos sind die Nummer-1-Peinlichkeit in der Buchhaltung und der häufigste
Grund, warum Unternehmen ein Abo-Tracking-Tool überhaupt einführen. Aktuell passiert genau das:
Man kann "Slack" und "slack" und "Slack Pro" als separate Einträge anlegen.
Diese Story liefert sofort sichtbaren Mehrwert ohne viel Infrastruktur zu benötigen.

**Acceptance Criteria:**
- [ ] Beim Speichern eines neuen Abos: Suche nach Abos mit gleichem `provider` (case-insensitive)
- [ ] Oder: Abo-Name ähnelt einem bestehenden Namen (Levenshtein-Distanz ≤ 2 oder Name-Substring)
- [ ] Wenn Duplikat erkannt: gelbe Warning-Box unter dem Formular ("Mögliches Duplikat: 'Slack' (€ 8,50/mo) existiert bereits")
- [ ] Warning ist nicht blockierend — User kann trotzdem speichern
- [ ] API: `GET /subscriptions/check-duplicate?name=X&provider=Y` für AJAX-Echtzeit-Check
- [ ] Subscription-Liste zeigt optional "Mögliche Duplikate"-Badge bei auffälligen Einträgen
- [ ] Nur innerhalb des eigenen Tenants geprüft

**Technical Notes:**
Neue Route in `subscriptions.py`. Fuzzy-Matching via Python `difflib.SequenceMatcher` (kein Extra-Package).
Frontend: `fetch()` im Formular mit 500ms Debounce auf Blur-Event von `name` und `provider`.

**Dependencies:** FR-004 (Subscription CRUD), FR-021 (Volltextsuche)

---

### STORY-053: Monatlicher Kosten-Report per E-Mail

**Epic:** EPIC-003 (Notifications & Automation)
**Priority:** Should Have
**Aufwand:** 3 Points

**User Story:**
Als **Admin** möchte ich **einmal im Monat eine E-Mail mit der Kostenübersicht erhalten**,
damit ich **ohne Dashboard-Login informiert bleibe und den Report direkt an die Buchhaltung weiterleiten kann**.

**Warum diese Story?**
Das ist passives Engagement — der höchste Aktivierungswert bei geringstem Aufwand.
Nicht jeder loggt sich täglich in ein SaaS-Tool ein. Eine monatliche E-Mail
mit "Ihr MRR ist von € 1.240 auf € 1.380 gestiegen, 3 neue Abos, 1 Kündigung"
hält den Nutzer im Loop und rechtfertigt das Produkt. Die gesamte Infrastruktur
(EmailService, Prefect, AnalyticsService) ist bereits vorhanden — das ist ein 3-Point-Story.

**Acceptance Criteria:**
- [ ] Jeder Tenant-Admin erhält am 1. des Monats (08:00 UTC) eine Kosten-Report-E-Mail
- [ ] E-Mail enthält: aktueller MRR, MRR-Veränderung vs. Vormonat, Anzahl aktiver Abos, Anzahl neuer Abos im Vormonat, Anzahl Kündigungen, Top-3 teuerste Abos, Link zum Dashboard
- [ ] HTML-Template in `app/templates/email/monthly_report.html`
- [ ] Neuer Prefect Flow `flows/monthly_report.py` (cron: `0 8 1 * *`)
- [ ] Neuer Internal-API Endpoint: `POST /internal/send-monthly-reports`
- [ ] Opt-out möglich: Setting `receive_monthly_report: bool` auf User-Ebene
- [ ] Nur an aktive Admins gesendet

**Technical Notes:**
Nutzt `AnalyticsService.summary()` und `mrr_history()`. Neuer Prefect Flow analog zu `renewal_reminder.py`.
E-Mail-Template mit Tabelle der Top-Abos. Opt-out Flag auf `User` Modell als `receive_monthly_report: bool = True`.

**Dependencies:** FR-010 (E-Mail), FR-014 (Analytics), FR-017 (Automation/Prefect)

---

> **Empfohlene Reihenfolge für Sprint 10:**
> 1. STORY-049 (Budget Alerts) — höchster Business-Value, bestehende Infra
> 2. STORY-050 (API Keys) — technische Enabler-Story für alle API-Nutzer
> 3. STORY-053 (Monthly Report) — schneller Win, 3 Points, hoher Engagement-Wert
> 4. STORY-052 (Duplicate Detection) — differenzierendes Feature, leicht umsetzbar
> 5. STORY-051 (Cost History) — nice-to-have, solide Datenbasis für künftige Charts

---

## Appendix A: Requirements Traceability Matrix

| Epic ID | Epic Name | Functional Requirements | Story Count (Est.) |
|---------|-----------|-------------------------|-------------------|
| EPIC-001 | Core Platform & Auth | FR-001, FR-002, FR-003, FR-008, FR-009, FR-011 | 8-10 |
| EPIC-002 | Subscription Management | FR-004, FR-005, FR-006, FR-012, FR-019, FR-025 | 8-10 |
| EPIC-003 | Notifications & Automation | FR-010, FR-016, FR-017 | 5-7 |
| EPIC-004 | Self-Service & Teams | FR-013, FR-018, FR-024 | 6-8 |
| EPIC-005 | Search, i18n & Data | FR-021, FR-022, FR-023 | 5-7 |
| EPIC-006 | Admin Dashboard & Quality | FR-007, FR-014, FR-015, FR-020 | 6-8 |
| EPIC-007 | Integrations | FR-026, FR-027, FR-030 | 5-7 |
| EPIC-008 | Security Upgrade | FR-028, FR-029, FR-031 | 5-7 |
| EPIC-009 | Production Readiness | FR-032, FR-033, FR-034, FR-035 | 4-6 |
| EPIC-010 | Icon System & NocoDB | FR-036, FR-037 | 3-5 |
| **TOTAL** | | **37 FRs** | **55-75 Stories** |

---

## Appendix B: Prioritization Details

### Functional Requirements

| Priority | Count | Percentage |
|----------|-------|------------|
| Must Have | 12 | 32% |
| Should Have | 14 | 38% |
| Could Have | 11 | 30% |
| **Total** | **37** | **100%** |

### Non-Functional Requirements

| Priority | Count | Percentage |
|----------|-------|------------|
| Must Have | 7 | 58% |
| Should Have | 5 | 42% |
| **Total** | **12** | **100%** |

### Epic Priority Distribution

| Priority | Epics | Est. Stories |
|----------|-------|-------------|
| Must Have | EPIC-001, 002, 003 | 21-27 |
| Should Have | EPIC-004, 005, 006 | 17-23 |
| Could Have | EPIC-007, 008, 009, 010 | 17-25 |
| **Total** | **10 Epics** | **55-75** |
