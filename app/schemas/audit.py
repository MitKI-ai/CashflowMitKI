from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str | None
    action: str
    entity_type: str
    entity_id: str
    old_values_json: str | None
    new_values_json: str | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
