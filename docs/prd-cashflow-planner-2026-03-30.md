# Product Requirements Document: Cashflow & Retirement Planner

**Date:** 2026-03-30
**Author:** Eddy
**Version:** 3.1
**Project Type:** Web Application (SaaS)
**Project Level:** Level 4 (40+ Stories)
**Status:** Planning Phase — Scope-Erweiterung vom Subscription Manager

**Vorgänger-PRD:** `docs/prd-subscription-manager-2026-03-27.md` (v2.0, 48 Stories / 230 Points delivered)

---

## Executive Summary

Das Produkt wird vom reinen **Subscription Manager** zum **persönlichen Finanzplaner** erweitert. Die bestehende Abo-Verwaltung wird zur Datengrundlage für ein vollständiges Cashflow-Management:

1. **Konten & Kontostände** — Girokonto, Sparkonto, Depot, Tagesgeld
2. **Daueraufträge & Lastschriften** — alle wiederkehrenden Ein- und Ausgaben
3. **Geld-Transfers** — Umbuchungen zwischen eigenen Konten
4. **Geldanlagen** — ETF-Sparpläne, Festgeld, Tagesgeld mit Rendite
5. **Haushaltsbuch** — manuelle Transaktionen tracken
6. **3 Sparziele** — Urlaub/Luxus, Notgroschen, Rente
7. **Cashflow-Prognose** — "Was bleibt am Monatsende?"
8. **Renten-Rechner** — "Was habe ich mit 67?" (nur mit Login)

### Produkt-Vision

> Von "Welche Abos habe ich?" zu "Kann ich mir meine Zukunft leisten?"

### Warum diese Erweiterung?

- **Subscription Manager allein** ist ein gesättigter Markt (Truebill, Bobby, Subly)
- **Cashflow + Rente + Haushaltsbuch** macht das Tool zum **persönlichen Finanzplaner**
- Die technische Basis (Multi-Tenant, Auth, Dashboard, Charts, E-Mail, i18n) steht
- YouTube-Showcase: "Wann bin ich finanziell frei?" ist massiv ansprechender Content

---

## Scope & Abgrenzung

### In Scope (v3.1)

| Bereich | Was |
|---------|-----|
| **Konten** | Girokonto, Sparkonto, Tagesgeld, Depot — Saldo, IBAN, Bankname |
| **Daueraufträge** | Wiederkehrende Überweisungen (Miete, Versicherung, Sparplan) |
| **Lastschriften** | Automatische Abbuchungen (Strom, Internet, Gym, etc.) |
| **Transfers** | Umbuchungen zwischen 2 eigenen Konten (Girokonto → Sparkonto) |
| **Geldanlagen** | ETF-Sparplan, Festgeld, Tagesgeld — mit erwarteter Rendite |
| **Haushaltsbuch** | Manuelle Transaktionen (Einkauf, Tanken, Geschenk, etc.) |
| **3 Sparziele** | Urlaub/Luxus, Notgroschen, Rente — mit Fortschritt + Prognose |
| **Cashflow-Dashboard** | Einnahmen vs. Ausgaben, Netto-Cashflow, Trend |
| **Renten-Rechner** | Zinseszins, Inflation, Szenarien (nur mit Login) |
| **Onboarding** | Konten → Daueraufträge → Lastschriften → Geldanlagen → Sparziele |
| **Testdaten** | Seed-Script für CI/CD mit realistischen Demo-Daten |

### Out of Scope

- Bankanbindung / Open Banking / PSD2 / FinTS
- Kryptowährungen / Aktien-Einzeltitel-Tracking
- Steuerberechnung / Steuerklassen-Rechner
- Kreditmanagement / Schuldentilgung
- Gemeinsame Haushalts-Planung (Multi-User-Cashflow)
- KI-basierte Empfehlungen ("Du könntest X kündigen")
- Öffentlicher Renten-Rechner ohne Login

---

## User Personas

### Persona 1: Lisa — Berufseinsteigerin (25)

- Erstes Gehalt, viele neue Abos, erstes Sparkonto
- Will wissen: "Wie viel kann ich sparen?" und "Lohnt sich ein ETF-Sparplan?"
- Nutzt die App auf dem Handy
- **Kernmotivation:** Kontrolle über Finanzen, Notgroschen aufbauen

### Persona 2: Markus — Familienvater (38)

- 2 Girokonten (er + Partnerin), Sparkonto, ETF-Depot
- Viele Daueraufträge (Miete, Kita, Versicherungen), Lastschriften (Strom, Internet)
- Will wissen: "Reicht die Rente?" und "Können wir uns den Urlaub leisten?"
- **Kernmotivation:** Familienfinanzen im Griff, Altersvorsorge planen

### Persona 3: Sandra — Freelancerin (42)

- Geschäftskonto + Privatkonto, schwankendes Einkommen
- Viele Business-Lastschriften (Adobe, Hosting, Versicherung)
- Will wissen: "Wie viel muss ich verdienen um X zu sparen?"
- **Kernmotivation:** Finanzielle Sicherheit trotz unregelmäßiger Einnahmen

---

## Datenmodell-Erweiterung

### Neue Entities

```
Account (Konto)
├── id (UUID)
├── tenant_id (FK → Tenant)
├── created_by_id (FK → User)
├── name ("Girokonto Sparkasse", "Tagesgeld ING", "ETF-Depot")
├── type (checking | savings | investment | deposit)
│     checking  = Girokonto
│     savings   = Sparkonto / Tagesgeld
│     investment = Depot (ETF, Aktien)
│     deposit   = Festgeld
├── bank_name ("Sparkasse", "ING", "Trade Republic")
├── iban (String, optional, verschlüsselt gespeichert)
├── balance (Decimal — aktueller Kontostand)
├── currency (EUR, CHF, USD)
├── is_primary (Boolean — Haupt-Girokonto für Cashflow)
├── interest_rate (Float — Zins p.a., für Tagesgeld/Festgeld)
├── is_active (Boolean)
├── notes (Text)
├── created_at / updated_at

StandingOrder (Dauerauftrag)
├── id (UUID)
├── tenant_id (FK → Tenant)
├── created_by_id (FK → User)
├── account_id (FK → Account — von welchem Konto)
├── name ("Miete", "Versicherung", "ETF-Sparplan")
├── type (expense | income | savings_transfer)
│     expense          = Ausgabe (Miete an Vermieter)
│     income           = Einnahme (Gehalt vom Arbeitgeber)
│     savings_transfer = Sparüberweisung auf eigenes Konto
├── recipient ("Vermieter GmbH", "Arbeitgeber AG")
├── amount (Decimal)
├── currency (EUR)
├── frequency (monthly | biweekly | quarterly | yearly)
├── execution_day (Integer 1-28 — Tag im Monat)
├── start_date (Date)
├── end_date (Date | null — null = unbefristet)
├── category_id (FK → Category, optional)
├── is_active (Boolean)
├── notes (Text)
├── created_at / updated_at

DirectDebit (Lastschrift)
├── id (UUID)
├── tenant_id (FK → Tenant)
├── created_by_id (FK → User)
├── account_id (FK → Account — von welchem Konto abgebucht)
├── name ("Strom EnBW", "Vodafone Internet", "Fitnessstudio")
├── creditor ("EnBW Energie", "Vodafone GmbH")
├── mandate_reference (String, optional — SEPA-Mandatsreferenz)
├── amount (Decimal — erwarteter Betrag, kann schwanken)
├── currency (EUR)
├── frequency (monthly | quarterly | yearly | irregular)
├── expected_day (Integer 1-28 — erwarteter Abbuchungstag)
├── category_id (FK → Category, optional)
├── is_active (Boolean)
├── notes (Text)
├── created_at / updated_at

Transfer (Umbuchung zwischen eigenen Konten)
├── id (UUID)
├── tenant_id (FK → Tenant)
├── created_by_id (FK → User)
├── from_account_id (FK → Account)
├── to_account_id (FK → Account)
├── amount (Decimal)
├── currency (EUR)
├── description ("Sparen", "ETF-Kauf", "Urlaubs-Rücklage")
├── transfer_date (Date)
├── is_recurring (Boolean)
├── frequency (monthly | quarterly | null)
├── savings_goal_id (FK → SavingsGoal, optional — Zuordnung zu Sparziel)
├── created_at

Investment (Geldanlage)
├── id (UUID)
├── tenant_id (FK → Tenant)
├── created_by_id (FK → User)
├── account_id (FK → Account — in welchem Depot/Konto)
├── name ("MSCI World ETF", "Festgeld 12M", "Tagesgeld ING")
├── type (etf_savings_plan | fixed_deposit | call_money | bonds | other)
│     etf_savings_plan = ETF-Sparplan
│     fixed_deposit    = Festgeld
│     call_money       = Tagesgeld
│     bonds            = Anleihen
│     other            = Sonstige
├── current_value (Decimal)
├── monthly_contribution (Decimal — monatliche Einzahlung)
├── expected_annual_return (Float — erwartete Rendite % p.a.)
├── start_date (Date)
├── maturity_date (Date | null — Fälligkeit bei Festgeld)
├── currency (EUR)
├── is_active (Boolean)
├── notes (Text)
├── created_at / updated_at

Transaction (Haushaltsbuch-Eintrag)
├── id (UUID)
├── tenant_id (FK → Tenant)
├── created_by_id (FK → User)
├── account_id (FK → Account)
├── type (income | expense | transfer_in | transfer_out)
├── amount (Decimal — immer positiv, Typ bestimmt Vorzeichen)
├── currency (EUR)
├── description ("Edeka Einkauf", "Tanken Shell", "Geburtstag Geschenk")
├── category_id (FK → Category, optional)
├── transaction_date (Date)
├── is_recurring (Boolean, default: false — einmalig)
├── tags (Text, JSON-Array: ["lebensmittel", "wocheneinkauf"])
├── created_at

SavingsGoal (Sparziel)
├── id (UUID)
├── tenant_id (FK → Tenant)
├── created_by_id (FK → User)
├── name ("Notgroschen", "Urlaub Mallorca", "Rente ETF")
├── type (emergency | vacation_luxury | retirement)
│     emergency        = Notgroschen (3-6 Monatsgehälter)
│     vacation_luxury  = Urlaub / Luxus / Anschaffungen
│     retirement       = Altersvorsorge / Rente
├── target_amount (Decimal | null)
├── current_amount (Decimal)
├── monthly_contribution (Decimal)
├── expected_annual_return (Float — 0% Notgroschen, 7% ETF)
├── linked_account_id (FK → Account, optional — zugeordnetes Konto)
├── linked_investment_id (FK → Investment, optional)
├── priority (1=hoch, 2=mittel, 3=niedrig)
├── target_date (Date | null)
├── currency (EUR)
├── is_active (Boolean)
├── created_at / updated_at

RetirementProfile (Rentenprofil)
├── id (UUID)
├── tenant_id (FK → Tenant)
├── user_id (FK → User, unique)
├── birth_year (Integer)
├── target_retirement_age (Integer, default: 67)
├── current_savings (Decimal — bereits angespartes Vermögen)
├── expected_pension (Decimal — gesetzliche Rente/Monat)
├── desired_monthly_income (Decimal — Wunsch-Einkommen in Rente)
├── expected_annual_return (Float, default: 5.0)
├── expected_inflation (Float, default: 2.0)
├── created_at / updated_at

CashflowSnapshot (monatlicher Snapshot)
├── id (UUID)
├── tenant_id (FK → Tenant)
├── user_id (FK → User)
├── month (Date — 1. des Monats)
├── total_income (Decimal)
├── total_fixed_expenses (Decimal — Daueraufträge + Lastschriften)
├── total_subscriptions (Decimal — Abos)
├── total_variable_expenses (Decimal — Haushaltsbuch)
├── total_savings (Decimal — Transfers zu Sparzielen)
├── net_cashflow (Decimal)
├── savings_rate (Float — %)
├── total_assets (Decimal — Summe aller Kontostände)
├── created_at
```

### Beziehungs-Diagramm

```
Tenant
├── Account[] ──────────────┐
│   ├── StandingOrder[]     │
│   ├── DirectDebit[]       │
│   ├── Transaction[]       │
│   └── Investment[]        │
├── Transfer[] ─────────────┤ (from_account + to_account)
├── SavingsGoal[] ──────────┤ (linked_account, linked_investment)
├── Subscription[] (bestehend)
├── RetirementProfile (1:1 pro User)
└── CashflowSnapshot[]
```

### Cashflow-Formel

```
Monatlicher Cashflow =
  + Σ Daueraufträge (type=income)          → Gehalt, Nebenjobs
  + Σ Einmalige Einnahmen (Transaktionen)
  - Σ Daueraufträge (type=expense)         → Miete, Versicherung
  - Σ Lastschriften                        → Strom, Internet
  - Σ Subscriptions                        → Netflix, Spotify (bestehend!)
  - Σ Variable Ausgaben (Transaktionen)    → Einkauf, Tanken
  - Σ Transfers (type=savings_transfer)    → Sparplan-Überweisungen
  ──────────────────────────────────────
  = Netto-Cashflow (frei verfügbar)
```

---

## Functional Requirements (Neue FRs)

Die bestehenden 37 FRs (FR-001 bis FR-037) bleiben gültig. Neue FRs beginnen bei FR-100.

---

### FR-100: Konten-Verwaltung (Account CRUD)

**Priority:** Must Have

**Description:**
User erfasst seine Bankkonten: Girokonto, Sparkonto, Tagesgeld, Depot. Jedes Konto hat Name, Typ, Bankname, optionale IBAN, Kontostand und Währung.

**Acceptance Criteria:**
- [ ] Konto erstellen: Name, Typ (checking/savings/investment/deposit), Bankname, Kontostand
- [ ] Konto bearbeiten und deaktivieren (nicht löschen wenn Transaktionen existieren)
- [ ] IBAN-Feld optional, wird nie in Logs oder API-Responses gezeigt
- [ ] Ein Konto als "Hauptkonto" markierbar (is_primary)
- [ ] Kontoliste mit Gesamtsaldo (Summe aller Konten)
- [ ] API: `GET/POST /api/v1/accounts`, `GET/PUT/DELETE /api/v1/accounts/{id}`
- [ ] Web-UI: `/accounts` mit Karten-Layout (ein Karte pro Konto)
- [ ] Tenant-Isolation auf allen Queries

**Dependencies:** FR-001 (Tenant), FR-003 (RBAC)

---

### FR-101: Daueraufträge-Verwaltung

**Priority:** Must Have

**Description:**
Wiederkehrende Überweisungen: Gehalt (Einnahme), Miete (Ausgabe), Sparplan-Überweisung. Jeder Dauerauftrag ist an ein Konto gebunden und hat Frequenz + Ausführungstag.

**Acceptance Criteria:**
- [ ] Dauerauftrag erstellen: Name, Typ (income/expense/savings_transfer), Betrag, Frequenz, Ausführungstag, Konto
- [ ] Dauerauftrag bearbeiten und deaktivieren
- [ ] Typen: Einnahme (Gehalt), Ausgabe (Miete), Spar-Überweisung (Girokonto→Sparkonto)
- [ ] Frequenz: monatlich, 2-wöchentlich, quartalsweise, jährlich
- [ ] Ausführungstag 1-28 (kein 29-31 wegen kurzer Monate)
- [ ] Optional: Kategorie zuweisen (bestehende Categories)
- [ ] API: `GET/POST /api/v1/standing-orders`, `GET/PUT/DELETE /api/v1/standing-orders/{id}`
- [ ] Web-UI: `/standing-orders` mit Einnahmen/Ausgaben-Gruppierung
- [ ] Normalisierung auf Monatsbasis für Cashflow-Berechnung

**Dependencies:** FR-100 (Konten)

---

### FR-102: Lastschriften-Verwaltung

**Priority:** Must Have

**Description:**
Automatische Abbuchungen durch Dritte: Strom, Internet, Versicherung, Fitnessstudio. Ähnlich wie Abos, aber separat verwaltet (andere Kündigungsfristen, SEPA-Mandat).

**Acceptance Criteria:**
- [ ] Lastschrift erstellen: Name, Gläubiger (Creditor), Betrag, Frequenz, erwarteter Tag, Konto
- [ ] Optionale Mandatsreferenz (SEPA)
- [ ] Betrag als "erwartet" markiert (kann bei Strom/Gas schwanken)
- [ ] Frequenz: monatlich, quartalsweise, jährlich, unregelmäßig
- [ ] Optional: Kategorie zuweisen
- [ ] API: `GET/POST /api/v1/direct-debits`, `GET/PUT/DELETE /api/v1/direct-debits/{id}`
- [ ] Web-UI: `/direct-debits`
- [ ] Integration in Cashflow-Berechnung als feste Ausgabe

**Dependencies:** FR-100 (Konten)

---

### FR-103: Transfers zwischen Konten

**Priority:** Must Have

**Description:**
Umbuchungen zwischen eigenen Konten: Girokonto → Sparkonto (Sparen), Girokonto → Depot (ETF-Kauf). Transfers sind keine Ausgaben — sie bewegen Geld zwischen eigenen Konten.

**Acceptance Criteria:**
- [ ] Transfer erstellen: Von-Konto, Nach-Konto, Betrag, Beschreibung, Datum
- [ ] Wiederkehrende Transfers (is_recurring + frequency) für Sparpläne
- [ ] Optional: Zuordnung zu einem Sparziel (savings_goal_id)
- [ ] Transfer darf nicht von und zum selben Konto gehen (Validierung)
- [ ] Kontostände werden NICHT automatisch angepasst (manuelles Tracking)
- [ ] API: `GET/POST /api/v1/transfers`, `GET/DELETE /api/v1/transfers/{id}`
- [ ] Web-UI: `/transfers`
- [ ] In Cashflow-Berechnung: Transfers sind neutral (kein Einnahme/Ausgabe)

**Dependencies:** FR-100 (Konten)

---

### FR-104: Geldanlagen-Verwaltung

**Priority:** Must Have

**Description:**
Geldanlagen erfassen: ETF-Sparpläne, Festgeld, Tagesgeld. Jede Anlage hat aktuellen Wert, monatlichen Beitrag und erwartete Rendite. Basis für Renten-Prognose.

**Acceptance Criteria:**
- [ ] Geldanlage erstellen: Name, Typ, aktueller Wert, monatlicher Beitrag, erwartete Rendite
- [ ] Typen: ETF-Sparplan, Festgeld, Tagesgeld, Anleihen, Sonstige
- [ ] Zuordnung zu einem Account (Depot/Sparkonto)
- [ ] Festgeld: Fälligkeitsdatum anzeigen
- [ ] ETF-Sparplan: monatlicher Beitrag + Renditeerwartung = Prognose
- [ ] Summe aller Geldanlagen als "Gesamtvermögen" auf Dashboard
- [ ] API: `GET/POST /api/v1/investments`, `GET/PUT/DELETE /api/v1/investments/{id}`
- [ ] Web-UI: `/investments`
- [ ] Rendite-Prognose: "In 10 Jahren: €XX.XXX" (Zinseszins)

**Dependencies:** FR-100 (Konten)

---

### FR-105: Haushaltsbuch (Transaktionen)

**Priority:** Must Have

**Description:**
Manuelle Erfassung einzelner Transaktionen: Einkauf, Tanken, Restaurant, Geschenk. Jede Transaktion hat Betrag, Beschreibung, Kategorie und Datum. Ermöglicht granulares Ausgaben-Tracking.

**Acceptance Criteria:**
- [ ] Transaktion erstellen: Typ (income/expense), Betrag, Beschreibung, Datum, Konto, Kategorie
- [ ] Schnell-Eingabe: Betrag + Beschreibung reichen, Rest ist optional
- [ ] Tags als JSON-Array (z.B. ["lebensmittel", "wocheneinkauf"])
- [ ] Transaktionsliste mit Filter: Datum-Range, Kategorie, Typ, Konto
- [ ] Monatliche Zusammenfassung: Summe pro Kategorie
- [ ] API: `GET/POST /api/v1/transactions`, `GET/DELETE /api/v1/transactions/{id}`
- [ ] Web-UI: `/transactions` mit Tages-Gruppierung
- [ ] Schnell-Add Button auf jeder Seite (Modal oder Sticky-Button)
- [ ] Integration in Cashflow als "variable Ausgaben"

**Dependencies:** FR-100 (Konten)

---

### FR-106: Sparziele (3 Typen)

**Priority:** Must Have

**Description:**
3 vordefinierte Sparziel-Typen mit unterschiedlicher Logik:

1. **Notgroschen** — Ziel: 3-6 Monatsgehälter, Rendite: 0-2% (Tagesgeld), Priorität 1
2. **Urlaub/Luxus** — Ziel: frei definierbar, Rendite: 0%, kurzfristig
3. **Rente** — Ziel: berechnet aus Rentenlücke, Rendite: 5-7% (ETF), langfristig

**Acceptance Criteria:**
- [ ] Sparziel erstellen: Name, Typ (emergency/vacation_luxury/retirement), Zielbetrag, aktueller Stand, monatlicher Beitrag
- [ ] Typ-spezifische Defaults: Notgroschen (0% Rendite), Urlaub (0%), Rente (5%)
- [ ] Fortschrittsbalken: aktuell/Ziel
- [ ] Prognose: "Ziel erreicht am DD.MM.YYYY" (mit Zinseszins für Rente)
- [ ] Verknüpfung mit Account möglich (linked_account_id)
- [ ] Verknüpfung mit Investment möglich (linked_investment_id)
- [ ] Notgroschen-Empfehlung: "Empfohlen: X€ (3 Monatsgehälter)"
- [ ] API: `GET/POST /api/v1/savings-goals`, `GET/PUT/DELETE /api/v1/savings-goals/{id}`
- [ ] Web-UI: `/savings` mit 3 Karten (je eine pro Typ)

**Dependencies:** FR-100 (Konten), FR-104 (Geldanlagen)

---

### FR-107: Cashflow-Dashboard

**Priority:** Must Have

**Description:**
Zentrales Dashboard: Netto-Cashflow aus allen Quellen (Daueraufträge + Lastschriften + Subscriptions + Transaktionen). Balkendiagramm, Sparquote, Trend.

**Acceptance Criteria:**
- [ ] KPI-Cards: Einnahmen (grün), Feste Ausgaben (rot), Variable Ausgaben (orange), Netto-Cashflow, Sparquote (%)
- [ ] Balkendiagramm: Einnahmen vs. feste Ausgaben vs. variable Ausgaben (Chart.js, 6 Monate)
- [ ] Ausgaben-Breakdown: Daueraufträge vs. Lastschriften vs. Abos vs. Haushaltsbuch (Doughnut)
- [ ] Sparquote-Ampel: < 10% rot, 10-20% gelb, > 20% grün
- [ ] Gesamtvermögen: Summe aller Kontostände + Geldanlagen
- [ ] Trend-Chart über 12 Monate (aus Snapshots)
- [ ] Service: `CashflowService` mit `summary()`, `monthly_breakdown()`, `by_category()`
- [ ] API: `GET /api/v1/cashflow/summary`
- [ ] Web-Route: `/cashflow`

**Dependencies:** FR-100-105

---

### FR-108: Renten-Rechner (nur mit Login)

**Priority:** Must Have

**Description:**
Interaktiver Renten-/Sparprognose-Rechner. Zieht Daten aus Geldanlagen und Sparziel "Rente". Berechnet Vermögensentwicklung bis zum Rentenalter.

**Acceptance Criteria:**
- [ ] Eingabemaske: Geburtsjahr, Ziel-Rentenalter, aktuelles Vermögen, Sparrate/Monat, Rendite (%), Inflation (%), gesetzliche Rente
- [ ] Daten werden vorausgefüllt aus RetirementProfile + SavingsGoal (type=retirement) + Investments
- [ ] Zinseszins-Formel: FV = PV × (1+r)^n + PMT × ((1+r)^n - 1) / r
- [ ] Area-Chart: Vermögensentwicklung über Jahre (Chart.js)
- [ ] Tabelle: Jahr | Einzahlungen | Zinsen | Gesamt | Inflationsbereinigt
- [ ] Rentenlücke: Wunsch-Einkommen - gesetzliche Rente = Lücke
- [ ] Benötigtes Kapital: Lücke × 12 × (85 - Rentenalter)
- [ ] 3 Szenarien: Pessimistisch (3%), Realistisch (5%), Optimistisch (7%)
- [ ] Slider für interaktives Anpassen (JavaScript, kein Reload)
- [ ] NUR mit Login erreichbar, kein öffentlicher Zugang
- [ ] Web-Route: `/retirement`
- [ ] API: `POST /api/v1/retirement/calculate`

**Dependencies:** FR-106 (Sparziele Typ Rente), FR-104 (Geldanlagen)

---

### FR-109: Cashflow-Onboarding Wizard (6 Schritte)

**Priority:** Must Have

**Description:**
Interaktiver 6-Schritt-Wizard für neue User. Fragt systematisch alle Finanzdaten ab.

**Schritte:**

#### Schritt 1: "Deine Konten"
- Hauptkonto anlegen (Girokonto): Name, Bank, Kontostand
- Weitere Konten hinzufügen (+Button): Sparkonto, Tagesgeld, Depot
- Quick-Buttons für deutsche Banken (Sparkasse, Volksbank, ING, DKB, Commerzbank)
- Feedback: "X Konten mit €XX.XXX Gesamtguthaben"

#### Schritt 2: "Deine Daueraufträge"
- Kacheln für häufige Daueraufträge: Gehalt (Einnahme), Miete, Versicherung, KFZ, Handyvertrag
- Pro Kachel: Betrag + Tag im Monat
- "Hab ich nicht" per Klick überspringen
- Einnahmen (Gehalt) separat hervorgehoben
- Running Total: "€X.XXX Einnahmen, €X.XXX Ausgaben"

#### Schritt 3: "Deine Lastschriften"
- Kacheln: Strom, Gas, Internet, GEZ, Fitnessstudio, Streaming (Netflix, Spotify)
- Betrag + erwarteter Tag
- "Hab ich nicht" per Klick
- Running Total: "€XXX/Monat Lastschriften"

#### Schritt 4: "Deine Geldanlagen"
- Kacheln: ETF-Sparplan, Tagesgeld, Festgeld, Bausparvertrag
- Pro Anlage: aktueller Wert + monatlicher Beitrag + erwartete Rendite
- "Noch keine Geldanlagen" Button zum Überspringen
- Feedback: "€XX.XXX angelegt — in 10 Jahren: ca. €XX.XXX"

#### Schritt 5: "Deine 3 Sparziele"
- 3 Karten (immer alle 3):
  1. **Notgroschen**: Zielbetrag (Empfehlung: 3× Gehalt), aktueller Stand
  2. **Urlaub/Luxus**: Zielbetrag, monatlicher Beitrag
  3. **Rente**: Geburtsjahr, Wunsch-Rentenalter, gesetzliche Rente
- Jede Karte kann mit einem Konto/Investment verknüpft werden
- Überspringbar pro Karte

#### Schritt 6: "Deine Finanz-Übersicht"
- Dashboard-Preview mit allen eingegebenen Daten:
  - Konten: X Konten, €XX.XXX Guthaben
  - Einnahmen: €X.XXX/Monat
  - Feste Ausgaben: €X.XXX/Monat (Daueraufträge + Lastschriften)
  - Netto-Cashflow: €X.XXX
  - Sparquote: XX%
  - Vermögen: €XX.XXX (Konten + Geldanlagen)
  - Renten-Preview: "Mit 67: ca. €XXX.XXX"
- "Dashboard starten!" Button → speichert alles
- Setzt `user.onboarding_cashflow_complete = True`

**Acceptance Criteria:**
- [ ] 6-Schritt-Progress-Bar
- [ ] Max 2 Pflichtfelder pro Schritt
- [ ] Jeder Schritt überspringbar
- [ ] Zurück-Navigation (Daten bleiben erhalten, Session/LocalStorage)
- [ ] Mobile-optimiert (große Touch-Targets)
- [ ] Wizard in < 5 Minuten abschließbar
- [ ] Nach Abschluss: alle Objekte in DB erstellt
- [ ] Erster CashflowSnapshot wird automatisch erstellt
- [ ] Nur für neue User (onboarding_cashflow_complete Flag)
- [ ] i18n: DE + EN

**Dependencies:** FR-100-106

---

### FR-110: Cashflow-Monatskalender

**Priority:** Should Have

**Description:**
Kalender/Timeline: zeigt für jeden Tag im Monat welche Einnahmen, Ausgaben, Lastschriften und Transfers fällig sind.

**Acceptance Criteria:**
- [ ] Kalender-Grid für aktuellen Monat
- [ ] Grün: Einnahmen (Gehalt am 27., Nebenjob am 15.)
- [ ] Rot: Ausgaben (Miete am 1., Strom am 5.)
- [ ] Blau: Transfers (Sparplan am 1.)
- [ ] Laufende Bilanz: "Nach Tag X: +€ X.XXX verfügbar"
- [ ] Monat-Navigation vor/zurück
- [ ] Responsive: vertikale Timeline auf Mobile
- [ ] Web-Route: `/cashflow/calendar`

**Dependencies:** FR-101, FR-102

---

### FR-111: Cashflow-Snapshots & Trend

**Priority:** Should Have

**Description:**
Monatliche Snapshots (Prefect-Job) für historische Trend-Ansicht.

**Acceptance Criteria:**
- [ ] CashflowSnapshot Model
- [ ] Prefect Flow: `monthly_cashflow_snapshot.py` (cron: `0 6 1 * *`)
- [ ] Snapshot: income, fixed_expenses, subscriptions, variable_expenses, savings, net_cashflow, savings_rate, total_assets
- [ ] API: `GET /api/v1/cashflow/history?months=12`
- [ ] Trend-Chart auf Cashflow-Dashboard
- [ ] Internal API: `POST /internal/create-cashflow-snapshots`

**Dependencies:** FR-107 (Cashflow-Dashboard)

---

### FR-112: "Was wäre wenn?"-Simulator

**Priority:** Could Have

**Description:**
Hypothetische Szenarien durchspielen ohne echte Daten zu ändern.

**Acceptance Criteria:**
- [ ] Slider-UI: Gehalt +/-, Ausgaben +/-, Sparrate +/-
- [ ] Live-Neuberechnung Cashflow + Renten-Prognose
- [ ] "Aktuell" vs. "Szenario" Vergleich nebeneinander
- [ ] Kein Speichern — rein explorativ
- [ ] Web-Route: `/cashflow/simulator`

**Dependencies:** FR-107, FR-108

---

### FR-113: Seed-Script für CI/CD Demo-Daten

**Priority:** Must Have

**Description:**
Python-Script das realistische Demo-Daten für alle neuen Entities generiert. Wird in CI/CD-Pipeline und für lokale Entwicklung verwendet.

**Acceptance Criteria:**
- [ ] Script: `scripts/seed_cashflow.py`
- [ ] Erstellt vollständiges Demo-Szenario für "Markus — Familienvater":
  - 3 Konten: Girokonto (€3.200), Sparkonto (€12.000), ETF-Depot (€28.000)
  - 5 Daueraufträge: Gehalt (+€4.500), Miete (-€1.200), Versicherung (-€320), KFZ (-€180), Sparplan (-€500)
  - 6 Lastschriften: Strom (-€85), Internet (-€45), GEZ (-€18,36), Fitnessstudio (-€35), Handy (-€25), Gas (-€65)
  - 3 Geldanlagen: MSCI World ETF (€28.000, +€500/M, 7%), Tagesgeld (€12.000, 2%), Festgeld 12M (€5.000, 3.5%)
  - 3 Sparziele: Notgroschen (€12.000/€15.000), Urlaub (€800/€3.000), Rente (€28.000/€500.000)
  - 20 Transaktionen: Einkauf, Tanken, Restaurant, etc. (letzter Monat)
  - RetirementProfile: Jahrgang 1988, Ziel 67, Rente €1.400
- [ ] Idempotent: kann mehrfach ausgeführt werden (löscht + erstellt neu)
- [ ] Aufrufbar via `python scripts/seed_cashflow.py`
- [ ] In `docker-compose.yml`: als Init-Container oder Startup-Command
- [ ] In CI/CD: `pytest` nutzt Seed-Daten oder eigene Fixtures

**Dependencies:** Alle neuen Models

---

## Non-Functional Requirements (Neue NFRs)

---

### NFR-100: Performance Finanz-Berechnungen

**Priority:** Must Have

- [ ] Cashflow-Summary für 12 Monate < 500ms
- [ ] Renten-Prognose (50 Jahre × 12 Monate) < 200ms
- [ ] Slider-Update (JavaScript) refresht Chart ohne Seitenreload
- [ ] Dashboard lädt mit 100+ Transaktionen in < 2s

---

### NFR-101: Finanz-Daten-Datenschutz

**Priority:** Must Have

- [ ] Alle Finanz-Queries filtern nach tenant_id (wie bestehende Entities)
- [ ] IBAN wird nie in Logs, API-Responses oder Error-Messages ausgegeben
- [ ] structlog loggt KEINE Betragsfelder (amount, salary, balance)
- [ ] Kein Caching von Finanz-Summaries in öffentlichen Endpoints
- [ ] IBAN-Feld in DB optional und nicht in Standard-API-Responses enthalten

---

### NFR-102: Onboarding UX

**Priority:** Must Have

- [ ] Max 2 Pflichtfelder pro Wizard-Schritt
- [ ] "Überspringen"-Button auf jedem Schritt
- [ ] Wizard in < 5 Minuten abschließbar
- [ ] Kein Schritt erfordert Scrollen auf Desktop (above-the-fold)
- [ ] Fortschritt wird bei Reload beibehalten (Session/LocalStorage)

---

## Epics

### Bestehende Epics (unverändert)

| Epic | Name | Status |
|------|------|--------|
| EPIC-001 | Core Platform & Auth | Done (Sprint 1-8) |
| EPIC-002 | Subscription Management | Done (Sprint 1-7) |
| EPIC-003 | Notifications & Automation | Done (Sprint 3-4) |
| EPIC-004 | Self-Service & Teams | Done (Sprint 5) |
| EPIC-005 | Search, i18n & Data | Done (Sprint 6) |
| EPIC-006 | Admin Dashboard & Quality | Done (Sprint 3, 7) |
| EPIC-007 | Integrations | Done (Sprint 7) |
| EPIC-008 | Security Upgrade | Done (Sprint 8) |
| EPIC-009 | Production Readiness | Done (Sprint 9) |
| EPIC-010 | Icon System & NocoDB | Done (Sprint 7) |

---

### EPIC-100: Konten & Zahlungsströme

**Description:**
Das Fundament des Finanzplaners: Bankkonten erfassen, Daueraufträge (Einnahmen + Ausgaben), Lastschriften und Transfers zwischen eigenen Konten. Ohne Konten gibt es keinen Cashflow.

**Functional Requirements:** FR-100, FR-101, FR-102, FR-103
**Story Count Estimate:** 6-8
**Priority:** Must Have

**Business Value:**
Konten sind der "Container" für alles Geld. Daueraufträge und Lastschriften sind 80% des Cashflows — wer die hat, hat das Bild. Transfers ermöglichen Spar-Tracking.

**Warum ein Epic?**
Die 4 Entities (Account, StandingOrder, DirectDebit, Transfer) hängen eng zusammen — Daueraufträge und Lastschriften referenzieren immer ein Konto, Transfers verbinden zwei Konten.

---

### EPIC-101: Geldanlagen & Vermögen

**Description:**
Geldanlagen erfassen (ETF, Festgeld, Tagesgeld), Rendite-Prognosen berechnen, Gesamtvermögen darstellen. Verknüpfung mit Konten und Sparzielen.

**Functional Requirements:** FR-104
**Story Count Estimate:** 2-3
**Priority:** Must Have

**Business Value:**
Geldanlagen sind der "Reichtums-Teil" — ohne sie ist der Renten-Rechner blind. User sehen nicht nur "was geht raus" sondern "was wächst".

---

### EPIC-102: Haushaltsbuch

**Description:**
Manuelle Transaktionen erfassen und kategorisieren. Tages- und Monatsansicht. Integration in Cashflow als "variable Ausgaben". Schnell-Eingabe für den Alltag.

**Functional Requirements:** FR-105
**Story Count Estimate:** 3-4
**Priority:** Must Have

**Business Value:**
Das Haushaltsbuch schließt die Lücke zwischen "festen" Kosten (Daueraufträge, Lastschriften, Abos) und der Realität (Einkauf, Tanken, Spontan-Käufe). Ohne Haushaltsbuch fehlen 20-40% der Ausgaben im Cashflow.

---

### EPIC-103: Sparziele & Rente

**Description:**
3 Sparziel-Typen (Notgroschen, Urlaub/Luxus, Rente) mit Fortschritts-Tracking und Prognose. Renten-Rechner mit Zinseszins, Inflation und Szenarien.

**Functional Requirements:** FR-106, FR-108
**Story Count Estimate:** 4-5
**Priority:** Must Have

**Business Value:**
Das emotionale Herz des Produkts — "Wann bin ich finanziell frei?" ist der Hook der User bindet. Die 3 Sparziel-Typen decken 90% aller Spar-Motivationen ab.

---

### EPIC-104: Cashflow Engine & Dashboard

**Description:**
Die Berechnung und Visualisierung: Cashflow-Summary, Balkendiagramm, Sparquote, Trend über 12 Monate. Zieht Daten aus allen Quellen (Konten, Daueraufträge, Lastschriften, Subscriptions, Transaktionen).

**Functional Requirements:** FR-107, FR-111
**Story Count Estimate:** 3-4
**Priority:** Must Have

**Business Value:**
Das Dashboard ist die "Startseite" — der erste Ort den User jeden Tag sehen. Wenn der Cashflow grün ist, fühlt sich der User gut. Wenn rot, handelt er.

---

### EPIC-105: Cashflow-Onboarding

**Description:**
6-Schritt-Wizard der neue User durch die komplette Finanz-Einrichtung führt: Konten → Daueraufträge → Lastschriften → Geldanlagen → Sparziele → Übersicht. Interaktiv, schnell, visuell ansprechend.

**Functional Requirements:** FR-109
**Story Count Estimate:** 4-6
**Priority:** Must Have

**Business Value:**
Der Onboarding-Wizard ist die "Eingangstür". Ohne gutes Onboarding gibt es keine aktivierten User. 80% der Churn passiert in den ersten 5 Minuten — der Wizard muss sofort Wert zeigen.

---

### EPIC-106: Advanced Features

**Description:**
Kalender-Ansicht (wann geht was rein/raus), Szenario-Simulator ("Was wäre wenn?"), CI/CD-Testdaten.

**Functional Requirements:** FR-110, FR-112, FR-113
**Story Count Estimate:** 4-5
**Priority:** Should Have / Could Have

**Business Value:**
Power-User-Features die Engagement und Retention steigern. Der Kalender ist täglich relevant, der Simulator macht Spaß. Testdaten ermöglichen schnelle Entwicklung.

---

## User Stories (Sprint 10-14)

### Sprint 10: Konten & Zahlungsströme (25 Points)

| Story | Titel | Points | Epic |
|-------|-------|--------|------|
| STORY-054 | Account Model + CRUD API + Web UI | 5 | EPIC-100 |
| STORY-055 | Standing Orders CRUD + Einnahmen/Ausgaben | 5 | EPIC-100 |
| STORY-056 | Direct Debits CRUD + SEPA-Felder | 5 | EPIC-100 |
| STORY-057 | Transfers zwischen Konten | 5 | EPIC-100 |
| STORY-058 | Seed Script (scripts/seed_cashflow.py) | 3 | EPIC-106 |
| STORY-059 | Navigation Update (Cashflow-Menü) | 2 | EPIC-104 |

---

### Sprint 11: Geldanlagen, Haushaltsbuch, Sparziele (24 Points)

| Story | Titel | Points | Epic |
|-------|-------|--------|------|
| STORY-060 | Investment CRUD + Rendite-Prognose | 5 | EPIC-101 |
| STORY-061 | Transaction CRUD (Haushaltsbuch) | 5 | EPIC-102 |
| STORY-062 | Schnell-Eingabe Modal + Kategorien-Filter | 3 | EPIC-102 |
| STORY-063 | Savings Goals (3 Typen) + Fortschritt | 5 | EPIC-103 |
| STORY-064 | Retirement Profile + Calculator | 8 | EPIC-103 |

*Hinweis: STORY-062 (Schnell-Eingabe) kann optional Transaktionen direkt vom Dashboard oder jeder Seite erfassen — ein Sticky-Button unten rechts öffnet ein Modal.*

---

### Sprint 12: Cashflow-Dashboard & Engine (22 Points)

| Story | Titel | Points | Epic |
|-------|-------|--------|------|
| STORY-065 | CashflowService + Summary API | 5 | EPIC-104 |
| STORY-066 | Cashflow-Dashboard Web UI + Charts | 8 | EPIC-104 |
| STORY-067 | Cashflow-Snapshots + Trend | 5 | EPIC-104 |
| STORY-068 | Monats-Zusammenfassung Haushaltsbuch | 3 | EPIC-102 |
| STORY-069 | Gesamtvermögen-Widget (Konten + Anlagen) | 2 | EPIC-101 |

*Hinweis: STORY-069 zeigt auf dem Dashboard die Summe aller Kontostände + Geldanlagen als "Gesamtvermögen"-KPI-Card.*

---

### Sprint 13: Onboarding-Wizard (24 Points)

| Story | Titel | Points | Epic |
|-------|-------|--------|------|
| STORY-070 | Onboarding Step 1-2: Konten + Daueraufträge | 5 | EPIC-105 |
| STORY-071 | Onboarding Step 3: Lastschriften | 3 | EPIC-105 |
| STORY-072 | Onboarding Step 4: Geldanlagen | 3 | EPIC-105 |
| STORY-073 | Onboarding Step 5: Sparziele (3 Karten) | 5 | EPIC-105 |
| STORY-074 | Onboarding Step 6: Übersicht + Abschluss | 5 | EPIC-105 |
| STORY-075 | Playwright E2E Tests für Onboarding | 3 | EPIC-105 |

---

### Sprint 14: Polish & Advanced (18 Points)

| Story | Titel | Points | Epic |
|-------|-------|--------|------|
| STORY-076 | Cashflow-Monatskalender | 5 | EPIC-106 |
| STORY-077 | "Was wäre wenn?"-Simulator | 5 | EPIC-106 |
| STORY-078 | Budget Alerts (Schwellenwert-Warnung) | 5 | EPIC-106 |
| STORY-079 | Monthly Cashflow Report E-Mail | 3 | EPIC-106 |

---

## Sprint-Übersicht (Roadmap)

| Sprint | Ziel | Points | Stories |
|--------|------|--------|---------|
| 1-9 | Subscription Manager (abgeschlossen) | 230 | 48 |
| **10** | Konten & Zahlungsströme | 25 | STORY-054 bis 059 |
| **11** | Geldanlagen, Haushaltsbuch, Sparziele | 24 | STORY-060 bis 064 |
| **12** | Cashflow-Dashboard & Engine | 22 | STORY-065 bis 069 |
| **13** | Onboarding-Wizard (6 Schritte) | 24 | STORY-070 bis 075 |
| **14** | Polish & Advanced | 18 | STORY-076 bis 079 |
| **Gesamt** | | **343** | **74 Stories** |

---

## Requirements Traceability (Neue FRs → Epics → Stories)

| Epic | FRs | Stories | Points |
|------|-----|---------|--------|
| EPIC-100 | FR-100, FR-101, FR-102, FR-103 | 054-057 | 20 |
| EPIC-101 | FR-104 | 060, 069 | 7 |
| EPIC-102 | FR-105 | 061, 062, 068 | 11 |
| EPIC-103 | FR-106, FR-108 | 063, 064 | 13 |
| EPIC-104 | FR-107, FR-111 | 059, 065-067 | 20 |
| EPIC-105 | FR-109 | 070-075 | 24 |
| EPIC-106 | FR-110, FR-112, FR-113 | 058, 076-079 | 21 |
| **Total** | **14 FRs** | **26 Stories** | **116 Points** |

---

## Seed-Script Spezifikation (scripts/seed_cashflow.py)

### Demo-Persona: "Markus — Familienvater, 38"

```python
# Konten
accounts = [
    {"name": "Girokonto Sparkasse", "type": "checking", "bank": "Sparkasse", "balance": 3200, "is_primary": True},
    {"name": "Tagesgeld ING", "type": "savings", "bank": "ING", "balance": 12000, "interest_rate": 2.0},
    {"name": "ETF-Depot Trade Republic", "type": "investment", "bank": "Trade Republic", "balance": 28000},
]

# Daueraufträge
standing_orders = [
    {"name": "Gehalt", "type": "income", "amount": 4500, "day": 27, "account": "Girokonto"},
    {"name": "Miete", "type": "expense", "amount": 1200, "day": 1, "account": "Girokonto"},
    {"name": "KFZ-Versicherung", "type": "expense", "amount": 85, "day": 1, "freq": "monthly"},
    {"name": "Haftpflicht", "type": "expense", "amount": 15, "day": 1, "freq": "monthly"},
    {"name": "ETF-Sparplan", "type": "savings_transfer", "amount": 500, "day": 1, "account": "Girokonto"},
    {"name": "Kindergeld", "type": "income", "amount": 250, "day": 5},
]

# Lastschriften
direct_debits = [
    {"name": "Strom EnBW", "creditor": "EnBW", "amount": 85, "day": 5},
    {"name": "Gas Stadtwerke", "creditor": "Stadtwerke", "amount": 65, "day": 5},
    {"name": "Vodafone Internet", "creditor": "Vodafone", "amount": 45, "day": 3},
    {"name": "GEZ Rundfunkbeitrag", "creditor": "ARD ZDF", "amount": 18.36, "freq": "monthly", "day": 15},
    {"name": "Fitnessstudio", "creditor": "McFit", "amount": 35, "day": 1},
    {"name": "Handy Telekom", "creditor": "Telekom", "amount": 25, "day": 10},
]

# Geldanlagen
investments = [
    {"name": "MSCI World ETF", "type": "etf_savings_plan", "value": 28000, "monthly": 500, "return": 7.0},
    {"name": "Tagesgeld ING", "type": "call_money", "value": 12000, "monthly": 0, "return": 2.0},
    {"name": "Festgeld 12M", "type": "fixed_deposit", "value": 5000, "monthly": 0, "return": 3.5},
]

# Sparziele
savings_goals = [
    {"name": "Notgroschen", "type": "emergency", "target": 15000, "current": 12000, "monthly": 200},
    {"name": "Sommerurlaub 2027", "type": "vacation_luxury", "target": 3000, "current": 800, "monthly": 150},
    {"name": "Altersvorsorge ETF", "type": "retirement", "target": 500000, "current": 28000, "monthly": 500, "return": 7.0},
]

# Transaktionen (letzter Monat)
transactions = [
    {"desc": "Edeka Wocheneinkauf", "amount": 87.50, "cat": "Lebensmittel", "type": "expense"},
    {"desc": "Tanken Shell", "amount": 65.00, "cat": "Auto", "type": "expense"},
    {"desc": "Amazon Bücher", "amount": 34.99, "cat": "Shopping", "type": "expense"},
    {"desc": "Restaurant Bella Italia", "amount": 58.00, "cat": "Essen gehen", "type": "expense"},
    {"desc": "Rewe Einkauf", "amount": 42.30, "cat": "Lebensmittel", "type": "expense"},
    {"desc": "DM Drogerie", "amount": 23.50, "cat": "Haushalt", "type": "expense"},
    {"desc": "Kino", "amount": 24.00, "cat": "Freizeit", "type": "expense"},
    {"desc": "Apotheke", "amount": 12.80, "cat": "Gesundheit", "type": "expense"},
    {"desc": "Bahnticket", "amount": 35.00, "cat": "Transport", "type": "expense"},
    {"desc": "Geburtstagsgeschenk", "amount": 45.00, "cat": "Geschenke", "type": "expense"},
    # ...
]

# Retirement Profile
retirement = {
    "birth_year": 1988, "target_age": 67,
    "current_savings": 28000, "expected_pension": 1400,
    "desired_income": 2500, "return": 5.0, "inflation": 2.0,
}
```

### CI/CD Integration

```yaml
# docker-compose.yml
services:
  app:
    command: >
      sh -c "python scripts/seed_cashflow.py --if-empty && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

```yaml
# .github/workflows/ci.yml
- name: Seed test data
  run: python scripts/seed_cashflow.py --force
```

---

## Functional Requirements (v4.0 — AI & Polish)

---

### FR-114: Inflationsbereinigung & Kaufkraft-Anzeige

**Priority:** Must Have

**Description:**
Alle Finanz-Prognosen (Renten-Rechner, Sparziel-Prognosen, Gesamtvermögens-Entwicklung) zeigen neben dem Nominalwert auch den inflationsbereinigten Realwert an.

**Acceptance Criteria:**
- [ ] Globaler Inflations-Parameter (default 2%, konfigurierbar in Settings)
- [ ] Renten-Rechner: Spalte "Inflationsbereinigt" in Tabelle + Area-Chart
- [ ] Kaufkraft-Badge: "In heutiger Kaufkraft: €XX.XXX" neben jedem Zukunftswert
- [ ] Sparziel-Prognose: "Dein Ziel von €10.000 entspricht in 5 Jahren €X.XXX Kaufkraft"
- [ ] Formel: `real_value = nominal_value / (1 + inflation_rate) ^ years`

**Dependencies:** FR-108 (Renten-Rechner)

---

### FR-115: 3-Szenarien-Vergleich Rente

**Priority:** Must Have

**Description:**
Renten-Rechner zeigt gleichzeitig 3 Szenarien: Pessimistisch (3%), Realistisch (5%), Optimistisch (7%). Visualisiert als 3 Linien im gleichen Chart.

**Acceptance Criteria:**
- [ ] 3 Berechnungen parallel (pessimistisch/realistisch/optimistisch)
- [ ] Konfigurierbare Rendite-Werte pro Szenario
- [ ] Area-Chart mit 3 überlagerten Flächen (rot/gelb/grün)
- [ ] Tabelle: 3 Spalten für Szenarien nebeneinander
- [ ] API: `GET /api/v1/retirement/scenarios` → Array mit 3 Ergebnissen

**Dependencies:** FR-108, FR-114

---

### FR-116: Steuer-Schätzung auf Kapitalerträge

**Priority:** Should Have

**Description:**
Abgeltungssteuer (26.375% inkl. Soli) auf Kapitalerträge wird bei allen Prognosen berücksichtigt. Zeigt Brutto- und Netto-Rendite.

**Acceptance Criteria:**
- [ ] Default: 26.375% (25% + 5.5% Soli), konfigurierbar
- [ ] Freistellungsauftrag: Freibetrag (default €1.000) wird abgezogen
- [ ] Renten-Rechner: "Nach Steuern: €XX.XXX" Zeile
- [ ] Investment-Übersicht: Unrealisierte Gewinne mit Steuer-Schätzung
- [ ] Toggle: "Steuern berücksichtigen" (default: an)

**Dependencies:** FR-108, FR-104

---

### FR-117: Dashboard Widget-System

**Priority:** Must Have

**Description:**
Modulares Dashboard mit konfigurierbaren Widgets. User wählt welche KPI-Cards, Charts und Listen angezeigt werden und in welcher Reihenfolge.

**Acceptance Criteria:**
- [ ] Widget-Registry: jedes Widget hat ID, Titel, Typ (kpi/chart/list), Größe (1x1/2x1/2x2)
- [ ] Verfügbare Widgets: Netto-Cashflow, Gesamtvermögen, Sparquoten-Ampel, Nächste 5 Zahlungen, Vermögens-Pie-Chart, Budget-Status, Sparziel-Fortschritt, Monats-Trend
- [ ] User-Konfiguration: welche Widgets, Reihenfolge (JSON in User-Profil oder eigene Tabelle)
- [ ] Drag & Drop Reorder (HTML5 Drag API oder SortableJS)
- [ ] "Widget hinzufügen" Dialog mit Vorschau
- [ ] 3 Preset-Layouts: "Sparer", "Familie", "Investor"
- [ ] Mobile: Widgets stacken vertikal, kein Drag & Drop

**Dependencies:** FR-107 (Cashflow-Dashboard)

---

### FR-118: LLM Provider Management

**Priority:** Must Have

**Description:**
User können ihren eigenen LLM API-Key hinterlegen. Unterstützt: Anthropic Claude (via Claude SDK), OpenRouter (OpenAI-kompatibel). Keys werden verschlüsselt gespeichert. Bring-Your-Own-Key Modell.

**Acceptance Criteria:**
- [ ] Model: `LLMProvider` — id, tenant_id, user_id, provider (anthropic/openrouter), api_key_encrypted, model_id, is_active, created_at
- [ ] API-Key Verschlüsselung: Fernet (symmetric) mit APP_SECRET_KEY
- [ ] Settings-Seite: Provider auswählen, API-Key eingeben, Test-Button ("Verbindung testen")
- [ ] Unterstützte Provider:
  - **Anthropic**: `anthropic` Python SDK, Modelle: claude-sonnet-4-20250514, claude-haiku-4-5-20251001
  - **OpenRouter**: OpenAI-kompatible API (`openai` SDK mit custom base_url), alle Modelle
- [ ] API-Key wird nur verschlüsselt in DB gespeichert, nie in Logs/Responses
- [ ] `GET /api/v1/llm/providers` — Liste konfigurierter Provider (ohne Key)
- [ ] `POST /api/v1/llm/providers` — Provider anlegen/aktualisieren
- [ ] `POST /api/v1/llm/test` — Verbindungstest mit kurzem Prompt
- [ ] `DELETE /api/v1/llm/providers/{id}` — Provider löschen

**Dependencies:** Keine

---

### FR-119: AI Chat Assistant — Entity CRUD via Chat

**Priority:** Must Have

**Description:**
Chat-Interface auf jeder eingeloggten Seite. User können per natürlicher Sprache Entities erstellen, bearbeiten, abfragen und löschen. Das LLM erhält strukturierte Tool-Definitionen für alle CRUD-Operationen und führt sie über Function Calling aus.

**Acceptance Criteria:**
- [ ] Chat-Bubble unten rechts (neben Schnell-Eingabe Button), ausklappbares Panel
- [ ] Unterstützte Aktionen per Chat:
  - Konten: "Erstelle ein Sparkonto bei der ING mit 5000€ Guthaben"
  - Daueraufträge: "Füge Gehalt 4500€ monatlich am 27. hinzu"
  - Lastschriften: "Strom 85€ am 5. jeden Monat"
  - Transaktionen: "Heute 45€ bei Rewe für Lebensmittel ausgegeben"
  - Investments: "ETF MSCI World, aktueller Wert 15000€, eingezahlt 12000€"
  - Sparziele: "Notgroschen auf 10000€ erhöhen"
  - Budget Alerts: "Warnung bei über 400€ Lebensmittel"
- [ ] LLM bekommt Tool-Definitionen (Function Calling / Tool Use):
  ```
  tools: [
    {name: "create_account", parameters: {name, type, bank_name, balance, ...}},
    {name: "create_standing_order", parameters: {name, type, amount, ...}},
    {name: "create_transaction", parameters: {description, amount, type, category, ...}},
    {name: "list_accounts", parameters: {}},
    {name: "update_savings_goal", parameters: {id, target_amount, ...}},
    ...
  ]
  ```
- [ ] Bestätigungs-Schritt: LLM zeigt Vorschau ("Ich würde folgendes erstellen: ..."), User bestätigt
- [ ] Chat-Historie pro Session (nicht persistiert)
- [ ] Kontext: aktuelle Konten, Cashflow-Summary werden als System-Prompt mitgegeben
- [ ] Fallback wenn kein LLM-Key: "Bitte konfiguriere einen API-Key in den Einstellungen"
- [ ] Rate-Limiting: max 50 Nachrichten pro Stunde pro User
- [ ] i18n: DE + EN

**Dependencies:** FR-118 (LLM Provider)

---

### FR-120: Kontoauszug-Import (PDF & CSV)

**Priority:** Must Have

**Description:**
User können Bank-Kontoauszüge als PDF oder CSV hochladen. Das System parst die Transaktionen, zeigt eine farblich markierte Vorschau, und lässt den User Einträge als Transaktionen, Lastschriften, Daueraufträge oder Transfers übernehmen.

**Acceptance Criteria:**
- [ ] Upload: Drag & Drop Zone oder File-Picker für PDF/CSV
- [ ] PDF-Parsing: Extrahiert Datum, Beschreibung, Betrag, Saldo aus gängigen deutschen Bankformaten (Sparkasse, Volksbank, ING, DKB, Commerzbank)
- [ ] CSV-Parsing: Spalten-Mapping (wie bestehendes Import-Feature), Auto-Detect Delimiter
- [ ] Vorschau-Tabelle:
  - Jede Zeile = eine geparste Position
  - Farbcode: Grün = bekannte Einnahme (Match mit StandingOrder), Rot = bekannte Ausgabe (Match mit DirectDebit/Subscription), Gelb = unbekannt
  - Matching: Fuzzy-Match auf Name/Beschreibung gegen bestehende StandingOrders, DirectDebits, Subscriptions
- [ ] Pro Zeile kann User:
  - Label/Kategorie ändern
  - Markieren als: "Einmalige Transaktion" (→ Transaction), "Wiederkehrend" (→ StandingOrder oder DirectDebit erstellen), "Transfer" (→ Transfer), "Ignorieren"
  - Bei "Wiederkehrend": Frequenz angeben (monatlich/quartalsweise/jährlich)
- [ ] Batch-Import: "Alle übernehmen" Button erstellt alle gewählten Entities
- [ ] Optional LLM-Unterstützung (wenn Key vorhanden): LLM kategorisiert unbekannte Positionen automatisch
- [ ] Import-Historie: welche Dateien wann importiert wurden (Duplikat-Erkennung)
- [ ] API: `POST /api/v1/import/bank-statement` (multipart upload)
- [ ] API: `POST /api/v1/import/bank-statement/confirm` (Batch-Bestätigung)
- [ ] Web-Route: `/import/bank-statement`

**Dependencies:** FR-100 (Konten), FR-118 (LLM — optional)

---

## Non-Functional Requirements (v4.0)

---

### NFR-103: LLM-Daten-Sicherheit

**Priority:** Must Have

- [ ] API-Keys verschlüsselt in DB (Fernet), nie im Klartext in Logs, Responses, oder Fehlerseiten
- [ ] LLM-Prompts enthalten keine IBAN, Kontonummern oder vollständige Beträge — nur aggregierte/anonymisierte Daten
- [ ] Chat-Historie wird NICHT in DB gespeichert — nur Session-basiert (RAM/LocalStorage)
- [ ] Rate-Limiting: 50 LLM-Calls/Stunde/User, 500/Tag/Tenant
- [ ] Timeout: LLM-Anfragen max 30 Sekunden

---

### NFR-104: Bank-Import Robustheit

**Priority:** Must Have

- [ ] PDF-Parsing graceful degradation: wenn Format unbekannt, Fehlermeldung statt Crash
- [ ] Max Upload-Größe: 10MB für PDF, 5MB für CSV
- [ ] Duplikat-Erkennung: gleiche Datei nicht doppelt importieren (Hash-Check)
- [ ] Unterstützte PDF-Formate: mindestens Sparkasse, ING, DKB — weitere nach Bedarf

---

## Epics (v4.0)

---

### EPIC-202: Inflationsbereinigung & Szenario-Vergleich

**Description:**
Alle Finanz-Prognosen mit Inflationsbereinigung und 3-Szenarien-Ansicht. Steuer-Schätzung auf Kapitalerträge.

**Functional Requirements:** FR-114, FR-115, FR-116

**Story Count Estimate:** 4-5 Stories

**Priority:** Must Have

**Business Value:**
Ohne Inflationsbereinigung sind Renten-Prognosen irreführend. 500.000€ in 30 Jahren klingt viel, hat aber nur ~300.000€ Kaufkraft. 3 Szenarien zeigen die Bandbreite. Steuer-Schätzung macht die Prognose realistisch. Diese Features machen den Unterschied zwischen "Spielzeug" und "seriöser Finanzplanung".

---

### EPIC-205: Dashboard Widgets & Personalisierung

**Description:**
Modulares Dashboard mit konfigurierbaren, verschiebbaren Widgets. Preset-Layouts für verschiedene User-Typen.

**Functional Requirements:** FR-117

**Story Count Estimate:** 4-5 Stories

**Priority:** Should Have

**Business Value:**
Jeder User hat andere Prioritäten. Ein Sparer will Sparquote und Sparziel-Fortschritt prominent. Ein Investor will Vermögens-Entwicklung. Personalisierung steigert Engagement und tägliche Nutzung. Visuell beeindruckend für YouTube-Showcase.

---

### EPIC-206: LLM Integration & Chat Assistant

**Description:**
Bring-Your-Own-Key LLM-Anbindung (Anthropic Claude SDK + OpenRouter). Chat-Interface für natürlichsprachliche CRUD-Operationen auf allen Finanz-Entities. Function Calling für strukturierte Aktionen.

**Functional Requirements:** FR-118, FR-119

**Story Count Estimate:** 6-7 Stories

**Priority:** Must Have

**Business Value:**
Game-Changer für UX. Statt durch Formulare zu klicken sagt der User "Gehalt 4500 monatlich am 27." und das LLM erstellt den Dauerauftrag. Senkt die Einstiegshürde massiv. Differenziert von jeder anderen Finanz-App. Perfekt für mitKI.ai Branding ("mit KI" = mit AI). Claude SDK als Primary, OpenRouter für Flexibilität.

**Warum ein Epic?**
LLM-Integration berührt Security (Key-Verschlüsselung), Backend (Tool-Definitionen, Streaming), Frontend (Chat-UI, Bestätigungs-Flow) und alle bestehenden Services (CRUD-Operationen). Komplex genug für 2 Sprints.

---

### EPIC-207: Smart Bank Statement Import

**Description:**
PDF- und CSV-Kontoauszüge hochladen, automatisch parsen, farblich markierte Vorschau mit Matching gegen bestehende Entities, und Batch-Import mit Entity-Erstellung.

**Functional Requirements:** FR-120

**Story Count Estimate:** 5-6 Stories

**Priority:** Must Have

**Business Value:**
Löst das #1 Onboarding-Problem: User haben Monate/Jahre an Finanzdaten in Kontoauszügen. Manuelles Eintippen ist unrealistisch. Import macht die App sofort nützlich — User sieht seine echte finanzielle Situation statt leere Dashboards. LLM-gestützte Kategorisierung ist der "wow"-Moment.

**Warum ein Epic?**
PDF-Parsing ist technisch komplex (verschiedene Bankformate). Matching-Engine, Vorschau-UI mit interaktiver Zuordnung, und Batch-Entity-Erstellung sind eigenständige Challenges. Optional LLM-Kategorisierung verbindet EPIC-206 und EPIC-207.

---

## User Stories (Sprint 15-18)

### Sprint 15: Inflationsbereinigung & Szenarien (24 Points)

| Story | Titel | Points | Epic |
|-------|-------|--------|------|
| STORY-080 | Inflations-Parameter + Kaufkraft-Berechnung | 3 | EPIC-202 |
| STORY-081 | Renten-Rechner 3-Szenarien (API + Chart) | 5 | EPIC-202 |
| STORY-082 | Steuer-Schätzung Kapitalerträge | 5 | EPIC-202 |
| STORY-083 | Dashboard Widget-System (Registry + Config) | 5 | EPIC-205 |
| STORY-084 | 8 Standard-Widgets implementieren | 3 | EPIC-205 |
| STORY-085 | Drag & Drop Reorder + 3 Presets | 3 | EPIC-205 |

### Sprint 16: LLM Provider & Key Management (22 Points)

| Story | Titel | Points | Epic |
|-------|-------|--------|------|
| STORY-086 | LLMProvider Model + Key-Verschlüsselung (Fernet) | 5 | EPIC-206 |
| STORY-087 | Anthropic Claude SDK Integration + Streaming | 5 | EPIC-206 |
| STORY-088 | OpenRouter Integration (OpenAI-kompatibel) | 3 | EPIC-206 |
| STORY-089 | Settings UI: Provider-Config + Test-Button | 3 | EPIC-206 |
| STORY-090 | Tool-Definitionen für alle Entities | 3 | EPIC-206 |
| STORY-091 | Chat UI Panel + Message-Flow | 3 | EPIC-206 |

### Sprint 17: AI Chat CRUD + Bank Import Basis (25 Points)

| Story | Titel | Points | Epic |
|-------|-------|--------|------|
| STORY-092 | Chat Entity CRUD: Konten, Daueraufträge, Lastschriften | 5 | EPIC-206 |
| STORY-093 | Chat Entity CRUD: Transaktionen, Investments, Sparziele | 5 | EPIC-206 |
| STORY-094 | Chat Bestätigungs-Flow + Kontext-Injection | 3 | EPIC-206 |
| STORY-095 | CSV Bank Statement Parser + Spalten-Mapping | 5 | EPIC-207 |
| STORY-096 | PDF Bank Statement Parser (PyMuPDF/pdfplumber) | 5 | EPIC-207 |
| STORY-097 | Import-Vorschau Tabelle + Farbcode-Matching | 2 | EPIC-207 |

### Sprint 18: Smart Import + Polish (20 Points)

| Story | Titel | Points | Epic |
|-------|-------|--------|------|
| STORY-098 | Fuzzy-Matching gegen bestehende Entities | 5 | EPIC-207 |
| STORY-099 | Entity-Erstellung aus Kontoauszug (Batch) | 5 | EPIC-207 |
| STORY-100 | LLM-gestützte Auto-Kategorisierung | 5 | EPIC-207 |
| STORY-101 | Import-Historie + Duplikat-Erkennung | 3 | EPIC-207 |
| STORY-102 | E2E Tests AI Chat + Import Flow | 2 | EPIC-207 |

---

## Requirements Traceability (v4.0 — Neue Epics)

| Epic | FRs | Stories | Points |
|------|-----|---------|--------|
| EPIC-202 | FR-114, FR-115, FR-116 | 080-082 | 13 |
| EPIC-205 | FR-117 | 083-085 | 11 |
| EPIC-206 | FR-118, FR-119 | 086-094 | 35 |
| EPIC-207 | FR-120 | 095-102 | 27 |
| **Total v4.0** | **7 FRs** | **23 Stories** | **91 Points** |

---

## Open Questions (beantwortet)

| Frage | Antwort |
|-------|---------|
| Renten-Rechner ohne Login? | **Nein** — nur mit Login |
| Haushaltsbuch? | **Ja** — manuelle Transaktionen tracken |
| Sparquote: Ausgabe oder Umbuchung? | **3 separate Sparziele**: Notgroschen, Urlaub/Luxus, Rente |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-27 | Initial PRD — Subscription Manager |
| 2.0 | 2026-03-30 | Implementation Status, 5 Sprint-10-Stories |
| 3.0 | 2026-03-30 | Scope-Erweiterung Cashflow & Retirement |
| 3.1 | 2026-03-30 | Konten, Daueraufträge, Lastschriften, Transfers, Geldanlagen, Haushaltsbuch. 7 neue Epics (EPIC-100-106). 14 FRs (FR-100-113). 26 Stories (STORY-054-079). Seed-Script für CI/CD. 6-Schritt-Onboarding. |
| **4.0** | **2026-03-30** | **AI & Polish: Inflationsbereinigung, 3-Szenarien-Rente, Steuer-Schätzung, Dashboard-Widgets, LLM Chat Assistant (Claude SDK + OpenRouter), Smart Bank Statement Import (PDF+CSV). 4 neue Epics (EPIC-202/205/206/207). 7 FRs (FR-114-120). 23 Stories (STORY-080-102). 91 Points. Sprint 15-18.** |

---

**This PRD was created using BMAD Method v6 — Phase 2 (Planning)**
