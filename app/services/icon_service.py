"""Icon Library Service — STORY-035 / STORY-040

Provides a curated set of service icons (inline SVG).
NocoDB icons are fetched on demand and merged with the static list.
"""
from functools import lru_cache

import httpx

from app.config import settings

# Curated icon set: id, name, SVG path data (simplified monochrome icons)
_ICONS = [
    {"id": "netflix", "name": "Netflix", "color": "#E50914"},
    {"id": "spotify", "name": "Spotify", "color": "#1DB954"},
    {"id": "adobe", "name": "Adobe", "color": "#FF0000"},
    {"id": "microsoft", "name": "Microsoft", "color": "#00A4EF"},
    {"id": "google", "name": "Google", "color": "#4285F4"},
    {"id": "amazon", "name": "Amazon", "color": "#FF9900"},
    {"id": "apple", "name": "Apple", "color": "#555555"},
    {"id": "slack", "name": "Slack", "color": "#4A154B"},
    {"id": "github", "name": "GitHub", "color": "#181717"},
    {"id": "gitlab", "name": "GitLab", "color": "#FC6D26"},
    {"id": "dropbox", "name": "Dropbox", "color": "#0061FF"},
    {"id": "notion", "name": "Notion", "color": "#000000"},
    {"id": "figma", "name": "Figma", "color": "#F24E1E"},
    {"id": "zoom", "name": "Zoom", "color": "#2D8CFF"},
    {"id": "hubspot", "name": "HubSpot", "color": "#FF7A59"},
    {"id": "salesforce", "name": "Salesforce", "color": "#00A1E0"},
    {"id": "jira", "name": "Jira", "color": "#0052CC"},
    {"id": "confluence", "name": "Confluence", "color": "#172B4D"},
    {"id": "intercom", "name": "Intercom", "color": "#1F8DED"},
    {"id": "stripe", "name": "Stripe", "color": "#635BFF"},
    {"id": "twilio", "name": "Twilio", "color": "#F22F46"},
    {"id": "sendgrid", "name": "SendGrid", "color": "#1A82E2"},
    {"id": "mailchimp", "name": "Mailchimp", "color": "#FFE01B"},
    {"id": "canva", "name": "Canva", "color": "#00C4CC"},
    {"id": "loom", "name": "Loom", "color": "#625DF5"},
    {"id": "miro", "name": "Miro", "color": "#FFD02F"},
    {"id": "linear", "name": "Linear", "color": "#5E6AD2"},
    {"id": "vercel", "name": "Vercel", "color": "#000000"},
    {"id": "netlify", "name": "Netlify", "color": "#00C7B7"},
    {"id": "cloudflare", "name": "Cloudflare", "color": "#F48120"},
    {"id": "aws", "name": "AWS", "color": "#FF9900"},
    {"id": "gcp", "name": "Google Cloud", "color": "#4285F4"},
    {"id": "azure", "name": "Microsoft Azure", "color": "#0078D4"},
    {"id": "digitalocean", "name": "DigitalOcean", "color": "#0080FF"},
    {"id": "heroku", "name": "Heroku", "color": "#430098"},
    {"id": "datadog", "name": "Datadog", "color": "#632CA6"},
    {"id": "sentry", "name": "Sentry", "color": "#362D59"},
    {"id": "postman", "name": "Postman", "color": "#FF6C37"},
    {"id": "docker", "name": "Docker", "color": "#2496ED"},
    {"id": "jetbrains", "name": "JetBrains", "color": "#000000"},
    {"id": "1password", "name": "1Password", "color": "#1A8CFF"},
    {"id": "lastpass", "name": "LastPass", "color": "#D32D27"},
    {"id": "dashlane", "name": "Dashlane", "color": "#0E353D"},
    {"id": "generic", "name": "Generisch", "color": "#6B7280"},
]


def _fetch_nocodb_icons() -> list[dict]:
    """Fetch custom icons from NocoDB. Returns empty list on any failure."""
    try:
        url = getattr(settings, "nocodb_api_url", "")
        token = getattr(settings, "nocodb_api_token", "")
        headers = {"xc-auth": token} if token else {}
        resp = httpx.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return []
        rows = resp.json().get("list", [])
        result = []
        for row in rows:
            icon_id = str(row.get("Id", ""))
            name = row.get("Name", "")
            color = row.get("Color", "#6B7280")
            svg = row.get("SVG") or _make_icon({"id": icon_id, "name": name, "color": color})["svg"]
            result.append({"id": f"nc-{icon_id}", "name": name, "color": color, "svg": svg})
        return result
    except Exception:
        return []


@lru_cache(maxsize=1)
def get_all_icons() -> list[dict]:
    nocodb = _fetch_nocodb_icons()
    static = [_make_icon(i) for i in _ICONS]
    return nocodb + static


def _make_icon(icon: dict) -> dict:
    color = icon["color"]
    name = icon["name"]
    initials = "".join(w[0].upper() for w in name.split()[:2])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">'
        f'<rect width="32" height="32" rx="6" fill="{color}"/>'
        f'<text x="16" y="21" text-anchor="middle" fill="white" '
        f'font-family="Arial,sans-serif" font-size="13" font-weight="bold">{initials}</text>'
        f'</svg>'
    )
    return {"id": icon["id"], "name": name, "color": color, "svg": svg}


def search_icons(query: str) -> list[dict]:
    if not query:
        return get_all_icons()
    q = query.lower()
    return [i for i in get_all_icons() if q in i["name"].lower() or q in i["id"].lower()]


def get_icon(icon_id: str) -> dict | None:
    for i in get_all_icons():
        if i["id"] == icon_id:
            return i
    return None
