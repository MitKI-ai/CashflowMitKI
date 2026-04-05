# System Setup mitKI.ai

> Last updated: 2026-02-23 (Coolify Container 111 hinzugefügt)

---

## Host Infrastructure (Proxmox)

| Property | Value |
|---|---|
| **Hostname** | `prox` / `prox.mox` |
| **Hardware** | GEEKOM MiniAir 11 |
| **CPU** | Intel Celeron N5095 @ 2.00GHz (4 Cores) |
| **RAM** | 8 GB (7.5 GiB usable) |
| **OS** | Debian GNU/Linux 12 (bookworm) |
| **Kernel** | 6.14.11-4-pve |
| **Storage** | `local-lvm` (LVM-Thin, primary), `local` (ISO/Templates) |
| **Proxmox UI** | https://prox.mox:8006 |
| **Proxmox IP** | `192.168.1.8` |

---

## Network

| Property | Value |
|---|---|
| **Subnet** | `192.168.1.0/24` |
| **Gateway** | `192.168.1.1` |
| **DNS** | Via Gateway |
| **Taboo Range** | `192.168.1.1` – `192.168.1.10` ⚠️ RESERVIERT |
| **External Access** | Cloudflare Zero Trust Tunnel (via Container 104) |
| **External Domain** | `mitki.ai` (Cloudflare DNS) |

---

## SSH Access (aiworker)

```bash
# Von Windows PC direkt in Container (via Jump Host):
ssh -J aiworker@prox.mox aiworker@<container-ip>

# Nur auf Proxmox Host:
ssh aiworker@prox.mox
# oder mit explizitem Key:
ssh -i ~/.ssh/proxmox_ed25519 aiworker@192.168.1.8
```

**Autorisierte Keys** (in `~/.ssh/authorized_keys` auf allen Containern):
- `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN7rpXriAOW6vzy5Xsuh4aaZ5uo6iUSqTA7bn2WOBMhO` – Eddy@DESKTOP-GF0T1I7
- `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJw0gRqlVrqXhZ2E6HI0qtt4TnWBOSXyaKfNs5eBolH9` – eddy@mitki.ai

**Sudoers auf Proxmox Host** (`/etc/sudoers.d/aiworker`):
```
aiworker ALL=(ALL) NOPASSWD: /usr/bin/pvesh *, /usr/sbin/pct *, /usr/sbin/qm *,
  /usr/sbin/pveam *, /usr/bin/apt *, /usr/bin/python3 *, /usr/bin/git *, /usr/bin/whoami
```

---

## Container Übersicht (LXC)

| ID | Name | IP | OS | Status | Port(s) | Dienst |
|----|------|----|----|--------|---------|--------|
| 102 | n8n | 192.168.1.10 | Debian 12 | Running | 5678 | n8n Automation |
| 103 | cal | 192.168.1.11 | Ubuntu | Running | 3000 | Cal.com |
| 104 | proxy | 192.168.1.12 | Ubuntu | Running | 80, 443 | Caddy + CF Tunnel |
| 106 | nocodb | 192.168.1.14 | Debian 12 | Running | 8080 | NocoDB |
| 107 | mcp | 192.168.1.15 | Debian 12 | Running | – | MCP Server Cluster |
| 109 | prefect | 192.168.1.16 | Debian 12.12 | Running | 4200 | Prefect Server |
| 110 | abo-manager| 192.168.1.17 | Debian 12 | Running | 8080 | Abo-Manager |
| 111 | coolify | 192.168.1.18 | Debian 12 | Running | 8000 | Coolify PaaS |
| 101 | OH-PROD | – | Ubuntu | Stopped | – | (inaktiv) |
| 105 | scriberr | – | Debian | Stopped | – | (inaktiv) |
| 108 | RustDesk | – | Debian | Stopped | – | (inaktiv) |

---

## Container 102 – n8n (192.168.1.10)

| Property | Value |
|---|---|
| **OS** | Debian 12 |
| **Dienst** | n8n Workflow Automation |
| **Port intern** | `5678` |
| **Extern erreichbar** | `https://n8n.mitki.ai` (via Caddy Proxy) |
| **Daten** | `/home/aiworker/` (oder Docker Volume) |
| **Start** | `systemctl` oder `docker-compose` (TODO: live verifizieren) |
| **SSH** | `ssh -J aiworker@prox.mox aiworker@192.168.1.10` |

---

## Container 103 – Cal.com (192.168.1.11)

| Property | Value |
|---|---|
| **OS** | Ubuntu |
| **Dienst** | Cal.com (Kalender / Buchungssystem) |
| **Port intern** | `3000` |
| **Extern erreichbar** | `https://cal.mitki.ai` (via Caddy Proxy) |
| **SSH** | `ssh -J aiworker@prox.mox aiworker@192.168.1.11` |

---

## Container 104 – Proxy (192.168.1.12)

| Property | Value |
|---|---|
| **OS** | Ubuntu |
| **Dienste** | Caddy (Reverse Proxy) + Cloudflare Tunnel |
| **Ports intern** | `80` (HTTP), `443` (HTTPS) |
| **Caddyfile Pfad** | `/etc/caddy/Caddyfile` |
| **SSH** | `ssh -J aiworker@prox.mox aiworker@192.168.1.12` |

**Caddyfile (Verified Routes — Stand 2026-02-23):**
```caddy
# Alle Blöcke nutzen http:// — TLS wird von Cloudflare terminiert.
# header_up X-Forwarded-Proto https ist PFLICHT gegen Redirect-Loops!

http://automatisch.mitki.ai {
    encode zstd gzip
    reverse_proxy 192.168.1.16:4200 {
        header_up X-Forwarded-Proto https
        header_up X-Real-IP {remote_host}
    }
}

http://n8n.mitki.ai {
    encode zstd gzip
    reverse_proxy 192.168.1.10:5678 {
        header_up X-Forwarded-Proto https
        header_up X-Real-IP {remote_host}
    }
}

http://cal.mitki.ai {
    encode zstd gzip
    reverse_proxy 192.168.1.11:3000 {
        header_up X-Forwarded-Proto https
        header_up X-Real-IP {remote_host}
    }
}

http://nocodb.mitki.ai {
    encode zstd gzip
    reverse_proxy 192.168.1.14:8080 {
        header_up X-Forwarded-Proto https
        header_up X-Real-IP {remote_host}
    }
}

http://coolify.mitki.ai {
    encode zstd gzip
    reverse_proxy 192.168.1.18:8000 {
        header_up X-Forwarded-Proto https
        header_up X-Real-IP {remote_host}
    }
}
```

> ✅ Caddyfile Route für `automatisch.mitki.ai` ist konfiguriert und leitet auf Port 4200 weiter.
> ⚠️ `header_up X-Forwarded-Proto https` **immer** setzen — sonst Redirect-Loop bei Laravel/Django/Node-Apps!

**Cloudflare Tunnel:**
- Tunnel-ID: `7323a7ef-4113-451e-8087-cb746c4343b0`, Name: `mitki-proxy`
- Tunnel-Config liegt in `/etc/cloudflared/config.yml` (Ubuntu-Service auf LXC 104)
- Jede Domain braucht einen **expliziten** `hostname`-Eintrag in `config.yml` — KEIN Wildcard!
- Struktur in `/etc/cloudflared/config.yml`:
```yaml
ingress:
  - hostname: n8n.mitki.ai
    service: http://127.0.0.1:80
  - hostname: cal.mitki.ai
    service: http://127.0.0.1:80
  - hostname: coolify.mitki.ai
    service: http://127.0.0.1:80
  # ... weitere Einträge ...
  - service: http_status:404   # catch-all MUSS am Ende stehen
```
- DNS CNAME anlegen (kein Dashboard nötig): `pct exec 104 -- cloudflared tunnel route dns 7323a7ef-4113-451e-8087-cb746c4343b0 neuer-dienst.mitki.ai`
- LXC 104 ist **nicht direkt per SSH erreichbar** → immer via `pct exec 104 -- bash -c '...'` vom Proxmox Host

---

## Container 106 – NocoDB (192.168.1.14)

| Property | Value |
|---|---|
| **OS** | Debian 12 |
| **Dienst** | NocoDB (No-Code Datenbank UI) |
| **Port intern** | `8080` |
| **Extern erreichbar** | `https://nocodb.mitki.ai` |
| **Daten** | Docker Volume oder `/opt/nocodb/` (TODO: live verifizieren) |
| **SSH** | `ssh -J aiworker@prox.mox aiworker@192.168.1.14` |

---

## Container 107 – MCP (192.168.1.15)

| Property | Value |
|---|---|
| **OS** | Debian 12 |
| **Dienst** | MCP Server Cluster (Model Context Protocol) |
| **Port intern** | – (TODO: live verifizieren) |
| **SSH** | `ssh -J aiworker@prox.mox aiworker@192.168.1.15` |

---

## Container 109 – Prefect (192.168.1.16)

| Property | Value |
|---|---|
| **OS** | Debian 12.12 |
| **Template** | `debian-12-standard_12.12-1_amd64.tar.zst` |
| **Storage** | `local-lvm` |
| **Cores** | 2 |
| **RAM** | 2048 MB |
| **Disk** | 8 GB |
| **Dienst** | Prefect Server (Workflow Orchestration) |
| **Port intern** | `4200` |
| **Extern erreichbar** | `https://automatisch.mitki.ai` |
| **Venv Pfad** | `/opt/prefect-venv/` |
| **Prefect Binary** | `/opt/prefect-venv/bin/prefect` |
| **Systemd Service** | `/etc/systemd/system/prefect-server.service` |
| **SSH** | `ssh -J aiworker@prox.mox aiworker@192.168.1.16` |

**Prefect Server starten (manuell):**
```bash
/opt/prefect-venv/bin/prefect server start --host 0.0.0.0
```

**Systemd Service Definition:**
```ini
[Unit]
Description=Prefect Server
After=network.target

[Service]
User=aiworker
WorkingDirectory=/home/aiworker
ExecStart=/opt/prefect-venv/bin/prefect server start --host 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Status prüfen:**
```bash
ssh -J aiworker@prox.mox aiworker@192.168.1.16
systemctl status prefect-server
```

> **Status**: ✅ Prefect Installation erfolgreich abgeschlossen! Service läuft als `aiworker` auf Port 4200.
> **Lessons Learned**: Eine ausführliche Zusammenfassung der Probleme (Berechtigungen, Zombies, SSH-Quoting) und den sauberen 'Happy Path' für zukünftige Setups gibt's hier: [`docs/prefect_setup_lessons_learned.md`](docs/prefect_setup_lessons_learned.md).

---

## Container 110 – Abo-Manager (192.168.1.17)

| Property | Value |
|---|---|
| **OS** | Debian 12 (Nesting=1) |
| **Dienst** | Abo-Manager (Subscription Tracker) |
| **Port intern** | `8080` |
| **Extern erreichbar** | *(geplant)* |
| **Software** | Docker & Docker Compose, SQLite |
| **Code Path** | `/home/aiworker/abo-manager` |
| **SSH** | `ssh -J aiworker@prox.mox aiworker@192.168.1.17` |

---

## Container 111 – Coolify (192.168.1.18)

| Property | Value |
|---|---|
| **OS** | Debian 12 (privilegiert, Nesting=1, keyctl=1) |
| **Dienst** | Coolify PaaS (Self-hosted Heroku/Netlify Alternative) |
| **Port intern** | `8000` (Dashboard) |
| **Extern erreichbar** | `https://coolify.mitki.ai` |
| **Software** | Docker & Docker Compose |
| **Code Path** | `/data/coolify/source/` |
| **Compose Start** | `docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d` |
| **SSH** | `ssh -J aiworker@prox.mox aiworker@192.168.1.18` |

> ⚠️ **containerd.io gehalten auf Version 1.7.27** (`apt-mark hold containerd.io`).
> runc >= 1.2.6 (in containerd.io 2.x) schlägt im LXC-Kontext fehl. Nicht upgraden!
> Details: [`docs/coolify_setup_lessons_learned.md`](docs/coolify_setup_lessons_learned.md)

---

## External URLs (Cloudflare → Caddy → Container)

| URL | Container | Interner Port |
|-----|-----------|---------------|
| https://automatisch.mitki.ai | 109 (prefect) | 4200 |
| https://n8n.mitki.ai | 102 (n8n) | 5678 |
| https://cal.mitki.ai | 103 (cal) | 3000 |
| https://nocodb.mitki.ai | 106 (nocodb) | 8080 |
| https://coolify.mitki.ai | 111 (coolify) | 8000 |
| https://prox.mox:8006 | Host | 8006 |

---

## Skills & Skripte

| Datei | Zweck |
|---|---|
| `skills/lxc_manager/SKILL.md` | Anleitung für LXC Container Management |
| `skills/lxc_manager/scripts/create_lxc.sh` | Neuen LXC Container anlegen |
| `skills/lxc_manager/scripts/setup_ssh_containers.sh` | SSH + aiworker auf Containern einrichten |
| `skills/lxc_manager/archive/109_prefect_setup.sh` | (Archiv) Der exakte `systemd` Setup-Code, der für Prefect funktionierte |
| `skills/lxc_manager/archive/110_abo_manager_docker_setup.sh` | (Archiv) Das Docker Compose Installation-Skript für Container 110 |
| `docs/coolify_setup_lessons_learned.md` | Lessons Learned: Coolify Setup (Docker runc-Bug, Redirect-Loop, Proxy-Architektur) |

---

## Backup Strategie
 
- Backups via **Proxmox Backup Jobs** auf Synology NAS (`BackupsMitKI`).
- **NFS Spezial-Konfiguration**:
  - Synology Squash: "Map all users to admin" (für unprivilegierte Container).
  - Proxmox Host: `tmpdir: /var/tmp` in `/etc/vzdump.conf` gesetzt (löst `rsync chown` / `Invalid argument` Fehler bei NFS).
- **Intervall**: Täglich, Aufbewahrung 7 Tage.
- Status: ✅ **Aktiv & Getestet**.

---

## TODOs / Offene Punkte

- [x] Prefect Installation abschließen (Permission-Problem lösen via `pct exec 109 -- chown`)
- [x] Prefect `systemd` Service aktivieren & testen
- [x] `automatisch.mitki.ai` live verifizieren (über Caddy Proxy)
- [x] Caddyfile live auslesen und hier eintragen
- [x] Backup Permissions (Synology Squash + vzdump.conf tmpdir) gelöst
- [x] Abo-Manager Container (110) inkl. Docker & GitHub CLI eingerichtet
- [x] Coolify Container (111) inkl. Docker & Reverse Proxy eingerichtet (`coolify.mitki.ai`)
- [ ] Redis-Config verifizieren (falls Prefect Redis nutzt)
- [ ] Docker-Compose Paths für n8n, NocoDB, Cal.com dokumentieren
- [ ] MCP Server Ports dokumentieren
