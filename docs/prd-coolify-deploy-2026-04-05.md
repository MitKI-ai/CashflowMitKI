# PRD: Coolify Auto-Deploy + PostgreSQL Migration

**Datum:** 2026-04-05
**Autor:** mitKI.ai
**Status:** Draft → Implementation

## Ziel

Ablösung des manuellen SSH-tar-Deploys auf CT110 durch automatischen Coolify-Deploy bei Git-Push. Gleichzeitige Migration SQLite → PostgreSQL.

## Entscheidungen (getroffen)

| Frage | Entscheidung |
|-------|-------------|
| Migration | Direkter Cut-over auf `www.cashflow.mitki.ai` |
| Routing/TLS | Caddy (CT104) + CF Tunnel bleiben, Upstream zeigt auf Coolify |
| Datenbank | PostgreSQL in Coolify (EPIC-213 jetzt umsetzen) |
| Git-Branch | `main` als Default + CI-Target + Coolify-Watch-Branch |

## Architektur

### Vorher
```
Cloudflare Tunnel → Caddy (CT104) → CT110:8080 (systemd uvicorn + SQLite)
```

### Nachher
```
Cloudflare Tunnel → Caddy (CT104) → CT111:<coolify-port> (Coolify/Traefik)
                                    → App Container (uvicorn)
                                    → Postgres Container (Coolify Resource)
```

## Arbeitspakete

### Phase 0 — Vorbereitung (Code-Änderungen vor Coolify-Setup)

- [ ] `requirements.txt`: `psycopg2-binary` aktivieren (aktuell auskommentiert)
- [ ] `app/database.py`: SQLite-PRAGMA ist schon gated — keine Änderung nötig
- [ ] Alembic-Migrations auf Postgres verifizieren (lokal mit Docker-Postgres testen)
- [ ] Branch `main` aus `master` erstellen, als GitHub Default setzen
- [ ] CI in `.github/workflows/ci.yml` triggert schon auf `main` ✓
- [ ] Commit + Push auf `main`

### Phase 1 — PostgreSQL in Coolify anlegen

- [ ] Coolify: Neue Resource → PostgreSQL 16
- [ ] DB-Name: `cashflow_prod`
- [ ] User/Password: autogeneriert (Coolify macht das)
- [ ] Internal Connection URL notieren: `postgresql://user:pass@<coolify-internal-host>:5432/cashflow_prod`

### Phase 2 — Daten-Export von CT110 → Postgres

Einmaliger Datentransfer der Prod-DB. Script benötigt:

- [ ] SSH auf CT110: `sqlite3 /home/aiworker/abo-manager/data/subscriptions.db .dump > /tmp/prod-dump.sql`
- [ ] SQLite-Dump zu Postgres-kompatiblem SQL konvertieren (pgloader oder Python-Script)
- [ ] Alternative: Alembic-Schema auf leerer Postgres anlegen + Daten-Export/Import per Python-Script pro Tabelle

**Empfehlung:** pgloader im Docker-Container (einfachster Weg).

### Phase 3 — Coolify Application anlegen

- [ ] Source: GitHub Repo `MitKI-ai/CashflowMitKI`, Branch `main`
- [ ] Build: Dockerfile (existiert)
- [ ] Port: `8000` (expose)
- [ ] Environment Variables (siehe Phase 4)
- [ ] Volume Mount: `/data` (für Uploads/Reports, nicht mehr für DB)
- [ ] Health Check: `/health` ✓ (ist schon im Dockerfile)
- [ ] Auto-Deploy on Push: aktivieren

### Phase 4 — Environment Variables

Aus `.env` auf CT110 übernehmen + Postgres-URL anpassen:

```env
APP_ENV=production
APP_SECRET_KEY=<aus CT110>
DATABASE_URL=postgresql://<user>:<pass>@<coolify-pg-host>:5432/cashflow_prod
APP_PORT=8000
IS_PRODUCTION=true
APP_BASE_URL=https://www.cashflow.mitki.ai
INTERNAL_API_KEY=<aus CT110>
JWT_SECRET_KEY=<aus CT110>
SMTP_HOST=<aus CT110>
SMTP_PORT=<aus CT110>
SMTP_USER=<aus CT110>
SMTP_PASSWORD=<aus CT110>
SMTP_FROM=noreply@cashflow.mitki.ai
ADMIN_EMAIL=admin@mitki.ai
ADMIN_PASSWORD=<aus CT110>
PREFECT_API_URL=http://192.168.1.16:4200/api
GOOGLE_CLIENT_ID=<aus CT110, falls genutzt>
GOOGLE_CLIENT_SECRET=<aus CT110, falls genutzt>
MICROSOFT_CLIENT_ID=<aus CT110, falls genutzt>
MICROSOFT_CLIENT_SECRET=<aus CT110, falls genutzt>
```

### Phase 5 — Dockerfile CMD anpassen

Aktuell: `python scripts/seed.py && uvicorn ...`
- Seed-Script läuft bei jedem Start → bei Postgres mit bestehenden Daten unerwünscht
- Alembic-Migrations müssen beim Start laufen

**Geplante Änderung:**
```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

Seed nur einmalig manuell triggern.

### Phase 6 — Erster Test-Deploy auf Staging-Subdomain

- [ ] Coolify Domain: `staging-cashflow.mitki.ai` (oder temporär `coolify.mitki.ai:<port>`)
- [ ] Smoke-Test: `/health`, `/login`, `/dashboard`
- [ ] Daten-Check: Admin-Login funktioniert, Subscriptions sichtbar

### Phase 7 — Cut-over auf www.cashflow.mitki.ai

**Ablauf (Downtime ca. 5 Min):**

1. CT110: `systemctl stop abo-manager` (stoppt Writes)
2. Finaler DB-Sync (pgloader erneut)
3. Caddy-Config auf CT104 anpassen (siehe unten)
4. `systemctl reload caddy` auf CT104
5. DNS/CF-Tunnel check
6. Smoke-Test auf `www.cashflow.mitki.ai`
7. CT110 bleibt 7 Tage als Fallback stehen (`systemctl disable abo-manager`)

### Phase 8 — Caddy-Config anpassen (CT104)

**Aktuelle Route** (zu finden in `/etc/caddy/Caddyfile` auf CT104):
```caddy
www.cashflow.mitki.ai {
    reverse_proxy 192.168.1.17:8080
}
```

**Neue Route** (Port hängt von Coolify-Labels ab):
```caddy
www.cashflow.mitki.ai, cashflow.mitki.ai {
    reverse_proxy 192.168.1.18:<coolify-published-port>
}
```

**Frage:** Coolify publiziert pro App einen Host-Port oder läuft intern Traefik? Muss beim Coolify-Setup geklärt werden. Wenn Traefik: Caddy proxied auf CT111 Traefik-Port (meist 80), und Traefik routet per Host-Header.

### Phase 9 — Monitoring + Rollback-Plan

**Rollback (wenn Cut-over fehlschlägt):**
1. Caddy-Config auf CT104 zurücksetzen (git revert)
2. `systemctl start abo-manager` auf CT110
3. Coolify-App pausieren

## Risiken

| Risiko | Mitigation |
|--------|-----------|
| SQLite → Postgres: Datentyp-Inkonsistenzen (Boolean, Date) | pgloader testet auf Staging-DB zuerst |
| Alembic `render_as_batch=True` (SQLite-only) | Postgres ignoriert das, aber neue Migrations ggf. ohne batch_alter_table |
| CT110-Writes während Cut-over verloren | systemctl stop VOR finalem Sync |
| Coolify-Port ändert sich bei Redeploy | Statischen Host-Port in Coolify konfigurieren |
| Prefect (CT109) ruft `INTERNAL_API_KEY`-Endpoints auf CT110 | Prefect-URL auf neue Coolify-URL umstellen |

## Manuelle Schritte (was DU machen musst)

### Vor Coolify-Setup
1. **SSH-Key auf Proxmox hinterlegen** (für DB-Export von CT110)
2. **.env von CT110 sichern**: `ssh aiworker@prox.mox "sudo pct exec 110 -- cat /home/aiworker/abo-manager/.env" > ~/cashflow-prod.env.backup`
3. **SQLite-Backup**: `ssh aiworker@prox.mox "sudo pct exec 110 -- cp /home/aiworker/abo-manager/data/subscriptions.db /tmp/prod-backup-$(date +%F).db"`
4. **Coolify-Zugang prüfen**: https://coolify.mitki.ai erreichbar?

### Während Coolify-Setup
(Mit Screenshots — ich sage dir pro Screen was rein muss)

### Nach Cut-over
1. **Caddy-Config auf CT104** anpassen (ich gebe dir den Diff)
2. **Prefect-Deployments auf CT109** prüfen (INTERNAL_API_URL neu)
3. **Cloudflare Analytics** checken (keine 5xx-Spitzen)

## Offene Fragen (für später)

- Backup-Strategie für Postgres (Coolify hat built-in S3-Backups)
- Observability: Logs aktuell nur in Coolify UI — ggf. Grafana/Loki später
- Multi-Instanz / Zero-Downtime-Deploy (aktuell: ein Container, kurze Restart-Downtime)
