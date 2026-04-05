from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, require_role
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_log(
    entity_type: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _admin=Depends(require_role(["admin"])),
):
    return AuditService.list(db, tenant_id=tenant_id, entity_type=entity_type, limit=limit)
