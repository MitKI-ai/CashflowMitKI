import hashlib
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.import_history import ImportHistory
from app.models.transaction import Transaction
from app.models.user import User
from app.services.bank_import import MAX_FILE_SIZE, BankImportService

router = APIRouter(prefix="/import", tags=["import-bank"])


@router.post("/bank-statement/parse")
async def parse_bank_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Duplicate detection
    file_hash = hashlib.sha256(content).hexdigest()
    existing = db.query(ImportHistory).filter(
        ImportHistory.tenant_id == tenant_id, ImportHistory.file_hash == file_hash
    ).first()
    is_duplicate = existing is not None

    filename = (file.filename or "").lower()
    if filename.endswith(".csv") or file.content_type == "text/csv":
        entries = BankImportService.parse_csv(content.decode("utf-8", errors="replace"))
    elif filename.endswith(".pdf") or file.content_type == "application/pdf":
        entries = BankImportService.parse_pdf(content)
        if not entries:
            raise HTTPException(status_code=400, detail="Could not parse PDF. Format not supported or file corrupted.")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV or PDF.")

    # Match against existing entities
    entries = BankImportService.match_entries(entries, db=db, tenant_id=tenant_id)

    # Record import history
    history = ImportHistory(
        tenant_id=tenant_id, user_id=current_user.id,
        filename=file.filename or "unknown",
        file_hash=file_hash, entry_count=len(entries),
    )
    db.add(history)
    db.commit()

    result = {"entries": entries, "total": len(entries)}
    if is_duplicate:
        result["duplicate"] = True
    return result


@router.get("/bank-statement/history")
def import_history(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    history = (
        db.query(ImportHistory)
        .filter(ImportHistory.tenant_id == tenant_id)
        .order_by(ImportHistory.created_at.desc())
        .all()
    )
    return [
        {"id": h.id, "filename": h.filename, "entry_count": h.entry_count,
         "created_at": h.created_at.isoformat()}
        for h in history
    ]


class ImportEntry(BaseModel):
    description: str
    amount: float
    date: str
    action: str  # transaction, standing_order, direct_debit, ignore
    category: str = ""
    frequency: str = "monthly"


class ConfirmImport(BaseModel):
    entries: list[ImportEntry]


@router.post("/bank-statement/confirm")
def confirm_import(
    data: ConfirmImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    created_transactions = 0
    created_standing_orders = 0
    created_direct_debits = 0
    ignored = 0

    for entry in data.entries:
        if entry.action == "ignore":
            ignored += 1
            continue

        if entry.action == "transaction":
            tx = Transaction(
                tenant_id=tenant_id, created_by_id=current_user.id,
                description=entry.description,
                amount=abs(entry.amount),
                type="expense" if entry.amount < 0 else "income",
                category=entry.category,
                transaction_date=date.fromisoformat(entry.date),
            )
            db.add(tx)
            created_transactions += 1

        elif entry.action == "standing_order":
            from app.models.account import Account
            from app.models.standing_order import StandingOrder
            acc = db.query(Account).filter(Account.tenant_id == tenant_id).first()
            so = StandingOrder(
                tenant_id=tenant_id, created_by_id=current_user.id,
                account_id=acc.id if acc else None,
                name=entry.description,
                type="income" if entry.amount > 0 else "expense",
                amount=abs(entry.amount),
                frequency=entry.frequency,
                execution_day=1,
            )
            db.add(so)
            created_standing_orders += 1

        elif entry.action == "direct_debit":
            from app.models.account import Account
            from app.models.direct_debit import DirectDebit
            acc = db.query(Account).filter(Account.tenant_id == tenant_id).first()
            dd = DirectDebit(
                tenant_id=tenant_id, created_by_id=current_user.id,
                account_id=acc.id if acc else None,
                name=entry.description,
                amount=abs(entry.amount),
                frequency=entry.frequency,
                expected_day=1,
            )
            db.add(dd)
            created_direct_debits += 1

    db.commit()

    return {
        "created_transactions": created_transactions,
        "created_standing_orders": created_standing_orders,
        "created_direct_debits": created_direct_debits,
        "ignored": ignored,
        "total_processed": len(data.entries),
    }


# ── LLM Categorization ──────────────────────────────────────────────

class CategorizeEntry(BaseModel):
    description: str
    amount: float


class CategorizeRequest(BaseModel):
    entries: list[CategorizeEntry]


@router.post("/bank-statement/categorize")
def categorize_entries(
    data: CategorizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    from app.core.encryption import decrypt_api_key
    from app.models.llm_provider import LLMProvider
    from app.services.llm_service import LLMService

    provider = (
        db.query(LLMProvider)
        .filter(LLMProvider.tenant_id == tenant_id, LLMProvider.is_active == True)
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="No active LLM provider configured")

    entries_text = "\n".join(
        f"- {e.description} ({e.amount}€)" for e in data.entries
    )
    prompt = f"""Kategorisiere die folgenden Kontoauszug-Positionen.
Antworte NUR mit einem JSON-Array. Jedes Element hat "description" und "category".
Kategorien: food, transport, housing, utilities, entertainment, health, insurance, education, clothing, dining, other.

Positionen:
{entries_text}"""

    api_key = decrypt_api_key(provider.api_key_encrypted)
    result = LLMService.chat(
        provider=provider.provider,
        api_key=api_key,
        model_id=provider.model_id,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )

    import json
    try:
        categories = json.loads(result.get("content", "[]"))
    except (json.JSONDecodeError, TypeError):
        categories = []

    return {"categories": categories, "model": result.get("model")}
