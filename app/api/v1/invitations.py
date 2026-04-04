"""Team Invitations API — STORY-026"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, get_current_tenant_id, require_role
from app.models.invitation import Invitation
from app.models.user import User
from app.models.tenant import Tenant
from app.services.email_service import EmailService
from app.core.security import hash_password

router = APIRouter(prefix="/invitations", tags=["invitations"])


class InviteCreate(BaseModel):
    email: EmailStr
    role: str = "user"


class AcceptInvite(BaseModel):
    token: str
    display_name: str
    password: str


class InvitationResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/", status_code=201, response_model=InvitationResponse)
def create_invitation(
    body: InviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    # Check for existing pending invite
    existing = (
        db.query(Invitation)
        .filter(
            Invitation.tenant_id == tenant_id,
            Invitation.email == body.email,
            Invitation.status == "pending",
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Pending invitation for this email already exists")

    inv = Invitation(
        tenant_id=tenant_id,
        invited_by_id=current_user.id,
        email=body.email,
        role=body.role,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    # Send email
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    accept_url = f"http://localhost/invite/{inv.token}"  # placeholder; real URL from request in prod
    EmailService.send_invitation(
        to=body.email,
        invited_by=current_user.display_name or current_user.email,
        tenant_name=tenant.name if tenant else "",
        accept_url=accept_url,
    )

    return inv


@router.get("/", response_model=list[InvitationResponse])
def list_invitations(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return db.query(Invitation).filter(Invitation.tenant_id == tenant_id).all()


@router.post("/accept")
def accept_invitation(
    body: AcceptInvite,
    db: Session = Depends(get_db),
):
    inv = db.query(Invitation).filter(Invitation.token == body.token).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if inv.status != "pending":
        raise HTTPException(status_code=410, detail="Invitation already used or revoked")
    if inv.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        inv.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="Invitation expired")

    user = User(
        tenant_id=inv.tenant_id,
        email=inv.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        role=inv.role,
    )
    db.add(user)
    inv.status = "accepted"
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "tenant_id": inv.tenant_id}


@router.delete("/{invitation_id}")
def revoke_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_id: str = Depends(get_current_tenant_id),
):
    inv = db.query(Invitation).filter(
        Invitation.id == invitation_id,
        Invitation.tenant_id == tenant_id,
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    inv.status = "revoked"
    db.commit()
    return {"ok": True}
