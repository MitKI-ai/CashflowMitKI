"""NotificationService — create and manage in-app notifications."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationService:

    @staticmethod
    def create(
        db: Session,
        tenant_id: str,
        user_id: str,
        title: str,
        message: str,
        type: str = "info",
        link: str | None = None,
    ) -> Notification:
        n = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            link=link,
        )
        db.add(n)
        db.commit()
        db.refresh(n)
        return n

    @staticmethod
    def list(db: Session, tenant_id: str, user_id: str, unread_only: bool = False) -> list[Notification]:
        q = db.query(Notification).filter(
            Notification.tenant_id == tenant_id,
            Notification.user_id == user_id,
        )
        if unread_only:
            q = q.filter(Notification.is_read == False)  # noqa: E712
        return q.order_by(Notification.created_at.desc()).limit(50).all()

    @staticmethod
    def unread_count(db: Session, tenant_id: str, user_id: str) -> int:
        return (
            db.query(Notification)
            .filter(
                Notification.tenant_id == tenant_id,
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .count()
        )

    @staticmethod
    def mark_read(db: Session, notif_id: str, user_id: str) -> Notification | None:
        n = db.query(Notification).filter(
            Notification.id == notif_id, Notification.user_id == user_id
        ).first()
        if n:
            n.is_read = True
            db.commit()
            db.refresh(n)
        return n

    @staticmethod
    def mark_all_read(db: Session, tenant_id: str, user_id: str) -> int:
        updated = (
            db.query(Notification)
            .filter(
                Notification.tenant_id == tenant_id,
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .all()
        )
        for n in updated:
            n.is_read = True
        db.commit()
        return len(updated)
