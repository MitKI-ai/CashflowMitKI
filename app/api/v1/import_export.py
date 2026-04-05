"""CSV / JSON Import + Export — STORY-032 / STORY-033"""
import csv
import io
import json
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_current_tenant_id
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(tags=["import-export"])

# Columns we recognise in CSV import (case-insensitive mapping)
_COL_MAP = {
    "name": "name",
    "provider": "provider",
    "cost": "cost",
    "kosten": "cost",
    "preis": "cost",
    "currency": "currency",
    "währung": "currency",
    "waehrung": "currency",
    "billing_cycle": "billing_cycle",
    "abrechnungszyklus": "billing_cycle",
    "status": "status",
    "start_date": "start_date",
    "startdatum": "start_date",
    "next_renewal": "next_renewal",
    "naechste_erneuerung": "next_renewal",
    "auto_renew": "auto_renew",
    "notes": "notes",
    "notizen": "notes",
}

_EXPORT_FIELDS = [
    "id", "name", "provider", "cost", "currency", "billing_cycle",
    "status", "start_date", "next_renewal", "auto_renew", "notes", "created_at",
]


# ── Export ────────────────────────────────────────────────────────────────────

@router.get("/export/csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    subs = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).order_by(Subscription.name).all()

    def generate():
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=_EXPORT_FIELDS, lineterminator="\n")
        writer.writeheader()
        yield buf.getvalue()
        for s in subs:
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=_EXPORT_FIELDS, lineterminator="\n")
            writer.writerow({f: str(getattr(s, f, "") or "") for f in _EXPORT_FIELDS})
            yield buf.getvalue()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=subscriptions.csv"},
    )


@router.get("/export/json")
def export_json(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    subs = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).order_by(Subscription.name).all()
    data = [
        {f: str(getattr(s, f, "") or "") for f in _EXPORT_FIELDS}
        for s in subs
    ]
    return data


# ── Import ────────────────────────────────────────────────────────────────────

def _parse_csv(content: bytes) -> tuple[list[str], list[dict]]:
    """Return (columns, rows) from CSV bytes."""
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    columns = reader.fieldnames or []
    rows = list(reader)
    return list(columns), rows


def _map_row(raw: dict) -> dict:
    """Map raw CSV row to subscription field dict."""
    out = {}
    for raw_key, value in raw.items():
        mapped = _COL_MAP.get(raw_key.strip().lower())
        if mapped and value is not None:
            out[mapped] = value.strip()
    return out


@router.post("/import/csv/preview")
async def import_csv_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    columns, rows = _parse_csv(content)
    mapped = [_map_row(r) for r in rows]
    return {"columns": columns, "rows": mapped}


@router.post("/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    content = await file.read()
    _, rows = _parse_csv(content)

    imported = 0
    skipped = 0
    errors = []

    for i, raw in enumerate(rows, start=2):
        mapped = _map_row(raw)
        name = mapped.get("name", "").strip()
        if not name:
            skipped += 1
            continue
        try:
            cost = float(mapped.get("cost", 0) or 0)
            start_date_raw = mapped.get("start_date", "")
            next_renewal_raw = mapped.get("next_renewal", "")
            sub = Subscription(
                tenant_id=tenant_id,
                created_by_id=current_user.id,
                name=name,
                provider=mapped.get("provider", ""),
                cost=cost,
                currency=mapped.get("currency", "EUR"),
                billing_cycle=mapped.get("billing_cycle", "monthly"),
                status=mapped.get("status", "active"),
                start_date=date.fromisoformat(start_date_raw) if start_date_raw else date.today(),
                next_renewal=date.fromisoformat(next_renewal_raw) if next_renewal_raw else None,
                auto_renew=mapped.get("auto_renew", "true").lower() != "false",
                notes=mapped.get("notes") or None,
            )
            db.add(sub)
            imported += 1
        except Exception as exc:
            errors.append({"row": i, "error": str(exc)})
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors}
