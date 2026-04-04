from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, get_current_user
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return NotificationService.list(db, tenant_id=tenant_id, user_id=current_user.id)


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    count = NotificationService.unread_count(db, tenant_id=tenant_id, user_id=current_user.id)
    return {"count": count}


@router.post("/", response_model=NotificationResponse, status_code=201)
def create_notification(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return NotificationService.create(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        title=data.title,
        message=data.message,
        type=data.type,
        link=data.link,
    )


@router.post("/{notif_id}/read", response_model=NotificationResponse)
def mark_read(
    notif_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = NotificationService.mark_read(db, notif_id=notif_id, user_id=current_user.id)
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    return n


@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    count = NotificationService.mark_all_read(db, tenant_id=tenant_id, user_id=current_user.id)
    return {"marked_read": count}
