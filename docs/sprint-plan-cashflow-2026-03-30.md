# Sprint Plan: Cashflow & Retirement Planner

**Date:** 2026-03-30
**Scrum Master:** Claude (AI)
**Project Level:** 4
**PRD:** `docs/prd-cashflow-planner-2026-03-30.md` (v3.1)
**Scope:** Sprint 10-12 (Sprint 13-14 werden separat geplant)

---

## Executive Summary

3 Sprints um den Subscription Manager zum Cashflow-Planner zu erweitern. Sprint 10 baut das Daten-Fundament (Konten, Daueraufträge, Lastschriften, Transfers). Sprint 11 vervollständigt alle Entities (Geldanlagen, Haushaltsbuch, Sparziele). Sprint 12 baut die Cashflow-Engine, das Dashboard und den Renten-Rechner.

**Key Metrics:**
- Stories: 18
- Points: 72
- Sprints: 3
- Capacity: ~25 points/sprint
- Historical Velocity: 26 (rolling avg over 9 sprints)

---

## Sprint 10: Konten & Zahlungsströme (23 Points)

**Goal:** Alle Bankkonten, Daueraufträge, Lastschriften und Transfers als CRUD verfügbar. Seed-Script für CI/CD. Navigation erweitert.

**Warum dieser Schnitt?** Account ist die Basis-Entity — alle anderen Entities (StandingOrder, DirectDebit, Transfer, Investment, Transaction) referenzieren ein Konto. Ohne Konten kein Cashflow.

---

### STORY-054: Account Model + CRUD API + Web UI (5 Points)

**Epic:** EPIC-100 · **Priority:** Must Have

**User Story:**
Als User möchte ich meine Bankkonten erfassen (Girokonto, Sparkonto, Depot),
damit ich eine vollständige Übersicht meiner Finanzen habe.

**Acceptance Criteria:**
- [ ] SQLAlchemy Model `Account` mit: id, tenant_id, created_by_id, name, type (checking/savings/investment/deposit), bank_name, iban (optional), balance, currency, is_primary, interest_rate, is_active, notes, timestamps
- [ ] Pydantic Schemas: `AccountCreate`, `AccountUpdate`, `AccountResponse` — IBAN nie in Response
- [ ] API: `GET/POST /api/v1/accounts`, `GET/PUT/DELETE /api/v1/accounts/{id}`
- [ ] `GET /api/v1/accounts` liefert Gesamtsaldo (Summe aller Konten)
- [ ] Web-UI: `/accounts` mit Karten-Layout (eine Karte pro Konto, Typ-Icon)
- [ ] Web-Formular: Konto erstellen/bearbeiten
- [ ] Tenant-Isolation auf allen Queries
- [ ] Alembic Migration
- [ ] 6+ Tests (CRUD + Tenant-Isolation + IBAN-Exclusion)

**Technical Notes:**
Model in `app/models/account.py`. Schema in `app/schemas/account.py`. API in `app/api/v1/accounts.py`. Web in `app/web/routes/pages.py` (oder eigene Route-Datei). Template `app/templates/pages/accounts.html`.

**Dependencies:** Keine

---

### STORY-055: Standing Orders CRUD (5 Points)

**Epic:** EPIC-100 · **Priority:** Must Have

**User Story:**
Als User möchte ich meine Daueraufträge erfassen (Gehalt, Miete, Versicherung, Sparplan),
damit ich weiß was monatlich fest reinkommt und rausgeht.

**Acceptance Criteria:**
- [ ] SQLAlchemy Model `StandingOrder` mit: id, tenant_id, created_by_id, account_id (FK→Account), name, type (income/expense/savings_transfer), recipient, amount, currency, frequency (monthly/biweekly/quarterly/yearly), execution_day (1-28), start_date, end_date, category_id, is_active, notes, timestamps
- [ ] Pydantic Schemas
- [ ] API: `GET/POST /api/v1/standing-orders`, `GET/PUT/DELETE /api/v1/standing-orders/{id}`
- [ ] API liefert monatlich normalisierte Summen (yearly÷12, quarterly÷3)
- [ ] Web-UI: `/standing-orders` mit Gruppierung nach Einnahmen/Ausgaben/Spar-Überweisungen
- [ ] Web-Formular mit Account-Dropdown und Kategorie-Auswahl
- [ ] Alembic Migration
- [ ] 6+ Tests

**Technical Notes:**
Normalisierung: `monthly_amount()` Property auf Model oder im Schema-Validator. Frequenz biweekly = ×2.17/Monat.

**Dependencies:** STORY-054 (Account)

---

### STORY-056: Direct Debits CRUD (5 Points)

**Epic:** EPIC-100 · **Priority:** Must Have

**User Story:**
Als User möchte ich meine Lastschriften erfassen (Strom, Internet, Versicherung),
damit alle automatischen Abbuchungen im Cashflow berücksichtigt werden.

**Acceptance Criteria:**
- [ ] SQLAlchemy Model `DirectDebit` mit: id, tenant_id, created_by_id, account_id (FK→Account), name, creditor, mandate_reference (optional), amount, currency, frequency (monthly/quarterly/yearly/irregular), expected_day (1-28), category_id, is_active, notes, timestamps
- [ ] Pydantic Schemas
- [ ] API: `GET/POST /api/v1/direct-debits`, `GET/PUT/DELETE /api/v1/direct-debits/{id}`
- [ ] Web-UI: `/direct-debits`
- [ ] Web-Formular mit Account-Dropdown
- [ ] Monatliche Normalisierung (wie Standing Orders)
- [ ] Alembic Migration
- [ ] 5+ Tests

**Dependencies:** STORY-054 (Account)

---

### STORY-057: Transfers zwischen Konten (3 Points)

**Epic:** EPIC-100 · **Priority:** Must Have

**User Story:**
Als User möchte ich Umbuchungen zwischen meinen Konten erfassen (Girokonto→Sparkonto),
damit ich Sparvorgänge tracken kann ohne sie als Ausgabe zu zählen.

**Acceptance Criteria:**
- [ ] SQLAlchemy Model `Transfer` mit: id, tenant_id, created_by_id, from_account_id, to_account_id, amount, currency, description, transfer_date, is_recurring, frequency, savings_goal_id (optional), created_at
- [ ] Validierung: from_account ≠ to_account
- [ ] Pydantic Schemas
- [ ] API: `GET/POST /api/v1/transfers`, `GET/DELETE /api/v1/transfers/{id}`
- [ ] Web-UI: `/transfers`
- [ ] In Cashflow neutral (kein Einnahme/Ausgabe)
- [ ] Alembic Migration
- [ ] 4+ Tests

**Dependencies:** STORY-054 (Account)

---

### STORY-058: Seed Script für CI/CD (3 Points)

**Epic:** EPIC-106 · **Priority:** Must Have

**User Story:**
Als Entwickler möchte ich mit einem Befehl realistische Demo-Daten laden,
damit ich Features schnell testen kann und die CI/CD-Pipeline Demo-Daten hat.

**Acceptance Criteria:**
- [ ] Script: `scripts/seed_cashflow.py`
- [ ] Erstellt Persona "Markus, 38": 3 Konten, 6 Daueraufträge, 6 Lastschriften, 10 bestehende Subscriptions
- [ ] Idempotent: `--force` Flag löscht + erstellt neu, ohne Flag nur wenn leer
- [ ] `python scripts/seed_cashflow.py` aufrufbar
- [ ] Erweitert bestehenden `scripts/seed.py` oder eigenständig
- [ ] Nutzt die gleichen Models wie die App
- [ ] 2+ Tests (Script-Import, Idempotenz)

**Technical Notes:**
Erstellt zunächst nur Account, StandingOrder, DirectDebit, Transfer — wird in Sprint 11 um Investment, Transaction, SavingsGoal erweitert.

**Dependencies:** STORY-054, 055, 056, 057

---

### STORY-059: Navigation Update (2 Points)

**Epic:** EPIC-104 · **Priority:** Must Have

**User Story:**
Als User möchte ich die neuen Cashflow-Seiten im Hauptmenü finden,
damit ich schnell zwischen den Bereichen navigieren kann.

**Acceptance Criteria:**
- [ ] Hauptnavigation: Dashboard | Abos | Konten | Cashflow | Sparen | Rente
- [ ] Mobile-Hamburger enthält alle neuen Links
- [ ] Aktiver Menüpunkt visuell hervorgehoben (CSS active state)
- [ ] i18n Labels DE + EN
- [ ] Links zeigen auf bestehende Seiten oder Platzhalter ("Kommt bald")

**Dependencies:** Keine

---

## Sprint 11: Geldanlagen, Haushaltsbuch, Sparziele (23 Points)

**Goal:** Alle verbleibenden CRUD-Entities fertig. Geldanlagen mit Rendite-Prognose. Haushaltsbuch mit Schnell-Eingabe. 3 Sparziel-Typen mit Fortschritt.

**Warum dieser Schnitt?** Nach Sprint 10 stehen Konten und wiederkehrende Zahlungen. Sprint 11 ergänzt Geldanlagen (Vermögensseite), Haushaltsbuch (variable Ausgaben) und Sparziele (Motivation). Danach sind ALLE Daten da für die Cashflow-Engine in Sprint 12.

---

### STORY-060: Investment CRUD + Rendite-Prognose (5 Points)

**Epic:** EPIC-101 · **Priority:** Must Have

**User Story:**
Als User möchte ich meine Geldanlagen erfassen (ETF, Festgeld, Tagesgeld),
damit ich mein Gesamtvermögen sehe und eine Rendite-Prognose bekomme.

**Acceptance Criteria:**
- [ ] SQLAlchemy Model `Investment` mit allen Feldern aus PRD
- [ ] Typen: etf_savings_plan, fixed_deposit, call_money, bonds, other
- [ ] Zuordnung zu Account (FK)
- [ ] Pydantic Schemas
- [ ] API: `GET/POST /api/v1/investments`, `GET/PUT/DELETE /api/v1/investments/{id}`
- [ ] API liefert `projected_value_10y` (Zinseszins-Berechnung)
- [ ] Web-UI: `/investments` mit Karten pro Anlage + Prognose
- [ ] Festgeld: Fälligkeitsdatum anzeigen
- [ ] Alembic Migration
- [ ] 5+ Tests

**Dependencies:** STORY-054 (Account)

---

### STORY-061: Transaction CRUD — Haushaltsbuch (5 Points)

**Epic:** EPIC-102 · **Priority:** Must Have

**User Story:**
Als User möchte ich einzelne Ausgaben und Einnahmen erfassen (Einkauf, Tanken, Restaurant),
damit ich auch variable Kosten im Cashflow berücksichtigen kann.

**Acceptance Criteria:**
- [ ] SQLAlchemy Model `Transaction` mit allen Feldern aus PRD
- [ ] Typen: income, expense, transfer_in, transfer_out
- [ ] Tags als JSON-Array in Text-Feld
- [ ] Pydantic Schemas
- [ ] API: `GET/POST /api/v1/transactions`, `GET/DELETE /api/v1/transactions/{id}`
- [ ] API Filter: `?date_from=&date_to=&category_id=&type=&account_id=`
- [ ] Web-UI: `/transactions` mit Tages-Gruppierung
- [ ] Alembic Migration
- [ ] 5+ Tests

**Dependencies:** STORY-054 (Account)

---

### STORY-062: Schnell-Eingabe Modal + Kategorien-Filter (3 Points)

**Epic:** EPIC-102 · **Priority:** Must Have

**User Story:**
Als User möchte ich Ausgaben mit 2 Klicks erfassen (Betrag + Beschreibung),
damit das Haushaltsbuch im Alltag nicht nervt.

**Acceptance Criteria:**
- [ ] Sticky-Button unten rechts auf allen eingeloggten Seiten ("+"-Icon)
- [ ] Klick öffnet Modal: Betrag (Pflicht) + Beschreibung (Pflicht) + Kategorie (optional) + Datum (default: heute)
- [ ] Submit via `fetch()` POST an `/api/v1/transactions` (kein Page-Reload)
- [ ] Erfolgs-Toast: "€ X.XX gespeichert"
- [ ] Kategorie-Dropdown im Transaktions-Filter auf `/transactions`
- [ ] Mobile: Modal nimmt volle Breite ein
- [ ] 3+ Tests

**Dependencies:** STORY-061 (Transaction CRUD)

---

### STORY-063: Savings Goals — 3 Typen + Fortschritt (5 Points)

**Epic:** EPIC-103 · **Priority:** Must Have

**User Story:**
Als User möchte ich 3 Sparziele verwalten (Notgroschen, Urlaub, Rente),
damit ich motiviert bleibe und meinen Fortschritt sehe.

**Acceptance Criteria:**
- [ ] SQLAlchemy Model `SavingsGoal` mit allen Feldern aus PRD
- [ ] 3 Typen: emergency (0% default), vacation_luxury (0%), retirement (5%)
- [ ] Fortschrittsbalken: current_amount / target_amount
- [ ] Prognose: "Ziel erreicht am DD.MM.YYYY" (Zinseszins für retirement)
- [ ] Notgroschen-Empfehlung basierend auf Gehalt (3× höchster income StandingOrder)
- [ ] Optional: linked_account_id, linked_investment_id
- [ ] API: `GET/POST /api/v1/savings-goals`, `GET/PUT/DELETE /api/v1/savings-goals/{id}`
- [ ] Web-UI: `/savings` mit 3 Karten (je eine pro Typ)
- [ ] Alembic Migration
- [ ] 6+ Tests

**Dependencies:** STORY-054 (Account), STORY-060 (Investment)

---

### STORY-068: Monats-Zusammenfassung Haushaltsbuch (3 Points)

**Epic:** EPIC-102 · **Priority:** Must Have

**User Story:**
Als User möchte ich sehen wie viel ich pro Kategorie im Monat ausgegeben habe,
damit ich Sparpotenziale erkenne.

**Acceptance Criteria:**
- [ ] API: `GET /api/v1/transactions/summary?month=2026-03`
- [ ] Response: `[{category: "Lebensmittel", total: 340.50, count: 8}, ...]`
- [ ] Auf `/transactions` Seite: Summary-Section oben mit Kategorie-Balken
- [ ] Monats-Navigation (vor/zurück)
- [ ] 3+ Tests

**Dependencies:** STORY-061 (Transaction CRUD)

---

### STORY-069: Gesamtvermögen-Widget (2 Points)

**Epic:** EPIC-101 · **Priority:** Must Have

**User Story:**
Als User möchte ich mein Gesamtvermögen auf einen Blick sehen,
damit ich weiß wo ich finanziell stehe.

**Acceptance Criteria:**
- [ ] API: `GET /api/v1/accounts/total-assets` → `{total_accounts: X, total_investments: Y, total: Z}`
- [ ] KPI-Card auf Dashboard (`/dashboard`): "Gesamtvermögen: €XX.XXX"
- [ ] Aufschlüsselung: Konten vs. Geldanlagen
- [ ] 2+ Tests

**Dependencies:** STORY-054 (Account), STORY-060 (Investment)

---

## Sprint 12: Cashflow Engine + Renten-Rechner (26 Points)

**Goal:** CashflowService aggregiert alle Datenquellen. Cashflow-Dashboard mit Charts und Sparquote. Renten-Rechner mit interaktiven Slidern und 3 Szenarien. Snapshots für Trend.

**Warum dieser Schnitt?** Alle CRUD-Entities sind nach Sprint 11 fertig. Sprint 12 baut die "Intelligenz" — der CashflowService berechnet den Netto-Cashflow aus 5+ Quellen, das Dashboard visualisiert ihn, und der Renten-Rechner gibt die langfristige Perspektive.

---

### STORY-065: CashflowService + Summary API (5 Points)

**Epic:** EPIC-104 · **Priority:** Must Have

**User Story:**
Als User möchte ich meinen monatlichen Netto-Cashflow berechnet bekommen,
damit ich weiß ob am Monatsende etwas übrig bleibt.

**Acceptance Criteria:**
- [ ] Service: `app/services/cashflow_service.py`
- [ ] `summary(tenant_id, user_id)` → berechnet:
  - total_income: Σ StandingOrders(type=income), normalisiert auf Monat
  - total_fixed_expenses: Σ StandingOrders(type=expense) + Σ DirectDebits
  - total_subscriptions: Σ Subscriptions(status=active), normalisiert auf Monat
  - total_variable_expenses: Σ Transactions(type=expense) im aktuellen Monat
  - total_savings: Σ StandingOrders(type=savings_transfer)
  - net_cashflow: income - fixed - subscriptions - variable - savings
  - savings_rate: (income > 0) ? (net_cashflow + savings) / income × 100 : 0
  - total_assets: Σ Account.balance + Σ Investment.current_value
- [ ] `monthly_breakdown(tenant_id, months=6)` → pro Monat die obigen Werte
- [ ] `by_category(tenant_id)` → Ausgaben gruppiert nach Kategorie
- [ ] API: `GET /api/v1/cashflow/summary`
- [ ] API: `GET /api/v1/cashflow/breakdown?months=6`
- [ ] Performance: < 500ms für 100+ Transaktionen
- [ ] 6+ Tests

**Dependencies:** STORY-054-063 (alle CRUDs)

---

### STORY-066: Cashflow-Dashboard Web UI + Charts (8 Points)

**Epic:** EPIC-104 · **Priority:** Must Have

**User Story:**
Als User möchte ich auf einen Blick sehen was reinkommt und rausgeht,
damit ich meinen Cashflow verstehe und Entscheidungen treffen kann.

**Acceptance Criteria:**
- [ ] Web-Route: `/cashflow`
- [ ] KPI-Cards: Einnahmen (grün), Feste Ausgaben (rot), Variable Ausgaben (orange), Netto-Cashflow (grün/rot), Sparquote (%)
- [ ] Sparquote-Ampel: < 10% rot, 10-20% gelb, > 20% grün
- [ ] Balkendiagramm: Einnahmen vs. Ausgaben (Chart.js, 6 Monate)
- [ ] Doughnut-Chart: Ausgaben-Breakdown (Daueraufträge vs. Lastschriften vs. Abos vs. Haushaltsbuch)
- [ ] Gesamtvermögen-KPI (aus STORY-069)
- [ ] Trend-Linie über verfügbare Snapshots (initial leer, wächst mit STORY-067)
- [ ] Responsive Layout (Cards stacken auf Mobile)
- [ ] Template: `app/templates/pages/cashflow.html`
- [ ] 4+ Tests

**Dependencies:** STORY-065 (CashflowService)

---

### STORY-064: Retirement Profile + Calculator (8 Points)

**Epic:** EPIC-103 · **Priority:** Must Have

**User Story:**
Als User möchte ich berechnen können was ich in der Rente haben werde,
damit ich weiß ob meine Sparstrategie ausreicht.

**Acceptance Criteria:**
- [ ] SQLAlchemy Model `RetirementProfile` (1:1 pro User)
- [ ] Web-Route: `/retirement` (nur mit Login)
- [ ] Eingabefelder: Geburtsjahr, Rentenalter (default 67), aktuelles Vermögen, Sparrate/Monat, Rendite (%), Inflation (%), gesetzliche Rente
- [ ] Felder vorausgefüllt aus: SavingsGoal(type=retirement), Investments, RetirementProfile
- [ ] Zinseszins: FV = PV × (1+r)^n + PMT × ((1+r)^n - 1) / r
- [ ] Area-Chart: Vermögensentwicklung über Jahre (Chart.js)
- [ ] Tabelle: Jahr | Einzahlungen kumuliert | Zinsen kumuliert | Gesamt | Inflationsbereinigt
- [ ] Rentenlücke: Wunsch-Einkommen - gesetzliche Rente = Lücke/Monat
- [ ] Benötigtes Kapital: Lücke × 12 × (85 - Rentenalter)
- [ ] 3 Szenarien gleichzeitig: Pessimistisch (3%), Realistisch (5%), Optimistisch (7%)
- [ ] JavaScript-Slider für Sparrate + Rendite (live Chart-Update, kein Reload)
- [ ] API: `POST /api/v1/retirement/calculate`, `GET/PUT /api/v1/retirement/profile`
- [ ] Alembic Migration
- [ ] 6+ Tests

**Dependencies:** STORY-063 (SavingsGoal), STORY-060 (Investment)

---

### STORY-067: Cashflow-Snapshots + Trend (5 Points)

**Epic:** EPIC-104 · **Priority:** Should Have

**User Story:**
Als User möchte ich sehen wie sich mein Cashflow über Monate entwickelt hat,
damit ich Verbesserungen oder Verschlechterungen erkenne.

**Acceptance Criteria:**
- [ ] SQLAlchemy Model `CashflowSnapshot` mit allen Feldern aus PRD
- [ ] Service: `CashflowService.create_snapshot(tenant_id, user_id)`
- [ ] Prefect Flow: `flows/monthly_cashflow_snapshot.py` (cron: `0 6 1 * *`)
- [ ] Internal API: `POST /internal/create-cashflow-snapshots`
- [ ] API: `GET /api/v1/cashflow/history?months=12`
- [ ] Trend-Chart auf `/cashflow` Dashboard (Line-Chart, 12 Monate)
- [ ] Erster Snapshot wird manuell bei Seed/Onboarding erstellt
- [ ] Alembic Migration
- [ ] 4+ Tests

**Dependencies:** STORY-065 (CashflowService)

---

## Epic Traceability

| Epic ID | Epic Name | Stories | Total Points | Sprint |
|---------|-----------|---------|--------------|--------|
| EPIC-100 | Konten & Zahlungsströme | 054, 055, 056, 057 | 18 | 10 |
| EPIC-101 | Geldanlagen & Vermögen | 060, 069 | 7 | 11 |
| EPIC-102 | Haushaltsbuch | 061, 062, 068 | 11 | 11 |
| EPIC-103 | Sparziele & Rente | 063, 064 | 13 | 11, 12 |
| EPIC-104 | Cashflow Engine & Dashboard | 059, 065, 066, 067 | 20 | 10, 12 |
| EPIC-106 | Advanced Features | 058 | 3 | 10 |

---

## FR Coverage

| FR ID | FR Name | Stories | Sprint |
|-------|---------|---------|--------|
| FR-100 | Konten-Verwaltung | STORY-054 | 10 |
| FR-101 | Daueraufträge | STORY-055 | 10 |
| FR-102 | Lastschriften | STORY-056 | 10 |
| FR-103 | Transfers | STORY-057 | 10 |
| FR-104 | Geldanlagen | STORY-060, 069 | 11 |
| FR-105 | Haushaltsbuch | STORY-061, 062, 068 | 11 |
| FR-106 | Sparziele | STORY-063 | 11 |
| FR-107 | Cashflow-Dashboard | STORY-065, 066 | 12 |
| FR-108 | Renten-Rechner | STORY-064 | 12 |
| FR-111 | Snapshots & Trend | STORY-067 | 12 |
| FR-113 | Seed Script | STORY-058 | 10 |

**Nicht in Sprint 10-12:** FR-109 (Onboarding → Sprint 13), FR-110 (Kalender → Sprint 14), FR-112 (Simulator → Sprint 14)

---

## Risks and Mitigation

**High:**
- Cashflow-Berechnung aus 5+ Quellen: Normalisierung (yearly, quarterly, biweekly → monthly) muss konsistent sein → **Mitigation:** Shared `normalize_to_monthly()` Utility, TDD
- Renten-Rechner JavaScript-Slider + Chart.js Live-Update: Client-side Complexity → **Mitigation:** Berechnung im JavaScript, kein Server-Roundtrip

**Medium:**
- 8 neue Alembic Migrations in 3 Sprints: Migration-Reihenfolge muss stimmen → **Mitigation:** Eine Migration pro Story, in Reihenfolge generieren
- Viele neue Web-Templates: Konsistenz mit bestehendem Design → **Mitigation:** base.html extends, bestehende Tailwind-Klassen wiederverwenden

**Low:**
- SQLite Performance bei 100+ Transaktionen: Queries könnten langsam werden → **Mitigation:** Indexes auf tenant_id + transaction_date, gemessen < 500ms

---

## Definition of Done

- [ ] Code implementiert und committed
- [ ] TDD: Tests zuerst geschrieben, dann Implementierung
- [ ] Mindestens 85% Coverage auf neuen Dateien
- [ ] Alembic Migration erstellt und getestet
- [ ] Tenant-Isolation verifiziert (Test mit 2 Tenants)
- [ ] IBAN/Beträge nicht in Logs
- [ ] i18n Labels DE + EN
- [ ] Responsive Layout getestet (Mobile + Desktop)
- [ ] API unter `/docs` (Swagger) dokumentiert

---

## Next Steps

Sprint 10 starten:
```
Sag "Go" für Sprint 10 — STORY-054 (Account CRUD) zuerst.
```

Sprint 13-14 (Onboarding + Polish) werden nach Sprint 12 geplant.

---

**This plan was created using BMAD Method v6 — Phase 4 (Implementation Planning)**
