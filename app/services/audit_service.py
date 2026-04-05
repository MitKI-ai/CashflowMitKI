"""AuditService — writes AuditLog entries and provides query access."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditService:

    @staticmethod
    def log(
        db: Session,
        tenant_id: str,
        user_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values_json=json.dumps(old_values) if old_values else None,
            new_values_json=json.dumps(new_values) if new_values else None,
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()
        return entry

    @staticmethod
    def list(
        db: Session,
        tenant_id: str,
        entity_type: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        q = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)
        if entity_type:
            q = q.filter(AuditLog.entity_type == entity_type)
        return q.order_by(AuditLog.created_at.desc()).limit(limit).all()
