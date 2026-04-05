import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    invited_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user")
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False,
                                       default=lambda: secrets.token_urlsafe(32))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, expired, revoked
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC) + timedelta(days=7)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
