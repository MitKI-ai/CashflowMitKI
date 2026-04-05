from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_api_key, encrypt_api_key
from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.llm_provider import LLMProvider
from app.models.user import User
from app.schemas.llm_provider import (
    VALID_PROVIDERS,
    LLMProviderCreate,
    LLMProviderResponse,
    LLMProviderUpdate,
)

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/providers", response_model=list[LLMProviderResponse])
def list_providers(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return (
        db.query(LLMProvider)
        .filter(LLMProvider.tenant_id == tenant_id)
        .order_by(LLMProvider.created_at.desc())
        .all()
    )


@router.post("/providers", response_model=LLMProviderResponse, status_code=201)
def create_provider(
    data: LLMProviderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    if data.provider not in VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider. Must be one of: {VALID_PROVIDERS}")

    provider = LLMProvider(
        tenant_id=tenant_id,
        user_id=current_user.id,
        provider=data.provider,
        api_key_encrypted=encrypt_api_key(data.api_key),
        model_id=data.model_id,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@router.put("/providers/{provider_id}", response_model=LLMProviderResponse)
def update_provider(
    provider_id: str,
    data: LLMProviderUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    provider = db.query(LLMProvider).filter(
        LLMProvider.id == provider_id, LLMProvider.tenant_id == tenant_id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if data.model_id is not None:
        provider.model_id = data.model_id
    if data.api_key is not None:
        provider.api_key_encrypted = encrypt_api_key(data.api_key)
    if data.is_active is not None:
        provider.is_active = data.is_active
    db.commit()
    db.refresh(provider)
    return provider


@router.delete("/providers/{provider_id}")
def delete_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    provider = db.query(LLMProvider).filter(
        LLMProvider.id == provider_id, LLMProvider.tenant_id == tenant_id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(provider)
    db.commit()
    return {"message": "Provider deleted"}


@router.post("/test")
def test_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    from app.services.llm_service import LLMService

    provider = (
        db.query(LLMProvider)
        .filter(LLMProvider.tenant_id == tenant_id, LLMProvider.is_active == True)
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="No active LLM provider configured")

    api_key = decrypt_api_key(provider.api_key_encrypted)
    result = LLMService.chat(
        provider=provider.provider,
        api_key=api_key,
        model_id=provider.model_id,
        messages=[{"role": "user", "content": "Sage 'OK' wenn du funktionierst."}],
        max_tokens=50,
    )
    return {"status": "ok", "model": result.get("model"), "response": result.get("content")}


@router.get("/tools")
def list_tools():
    from app.services.chat_tools import TOOL_DEFINITIONS
    return TOOL_DEFINITIONS


class ChatRequest(BaseModel):
    message: str
    auto_execute: bool = False


def _build_context(db: Session, tenant_id: str) -> str:
    """Build financial context for the system prompt."""
    from app.models.account import Account
    from app.models.investment import Investment
    from app.services.cashflow import CashflowService

    accounts = db.query(Account).filter(Account.tenant_id == tenant_id, Account.is_active == True).all()
    investments = db.query(Investment).filter(Investment.tenant_id == tenant_id, Investment.is_active == True).all()
    summary = CashflowService.monthly_summary(db, tenant_id=tenant_id)

    ctx_parts = ["Aktueller Finanz-Kontext des Users:"]
    if accounts:
        ctx_parts.append(f"Konten: {', '.join(f'{a.name} ({a.type}, {a.balance}€)' for a in accounts)}")
    if investments:
        ctx_parts.append(f"Anlagen: {', '.join(f'{i.name} ({i.current_value}€)' for i in investments)}")
    ctx_parts.append(f"Cashflow: Einnahmen {summary['monthly_income']}€, Ausgaben {summary['monthly_expenses']}€, Netto {summary['monthly_net']}€")
    return "\n".join(ctx_parts)


@router.post("/chat")
def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    from app.services.chat_executor import ChatExecutor
    from app.services.chat_tools import TOOL_DEFINITIONS
    from app.services.llm_service import LLMService

    provider = (
        db.query(LLMProvider)
        .filter(LLMProvider.tenant_id == tenant_id, LLMProvider.is_active == True)
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="No active LLM provider configured")

    api_key = decrypt_api_key(provider.api_key_encrypted)
    context = _build_context(db, tenant_id)
    system_prompt = LLMService.SYSTEM_PROMPT + "\n\n" + context

    result = LLMService.chat(
        provider=provider.provider,
        api_key=api_key,
        model_id=provider.model_id,
        messages=[{"role": "user", "content": data.message}],
        tools=TOOL_DEFINITIONS,
        system_prompt=system_prompt,
    )

    # If tool calls and auto_execute, run them
    tool_results = None
    if result.get("tool_calls") and data.auto_execute:
        tool_results = []
        for tc in result["tool_calls"]:
            tr = ChatExecutor.execute(
                tc["name"], tc["input"],
                db=db, tenant_id=tenant_id, user_id=current_user.id,
            )
            tool_results.append({"tool": tc["name"], "result": tr})

        # Send tool results back to LLM for final response
        import json
        messages = [
            {"role": "user", "content": data.message},
            {"role": "assistant", "content": result.get("content") or json.dumps([
                {"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["input"]}
                for tc in result["tool_calls"]
            ])},
            {"role": "user", "content": json.dumps([
                {"type": "tool_result", "tool_use_id": tc["id"], "content": json.dumps(tr["result"])}
                for tc, tr in zip(result["tool_calls"], tool_results)
            ])},
        ]
        final = LLMService.chat(
            provider=provider.provider,
            api_key=api_key,
            model_id=provider.model_id,
            messages=messages,
        )
        return {
            "response": final.get("content"),
            "tool_results": tool_results,
            "model": result.get("model"),
        }

    return {
        "response": result.get("content"),
        "tool_calls": result.get("tool_calls"),
        "model": result.get("model"),
    }
