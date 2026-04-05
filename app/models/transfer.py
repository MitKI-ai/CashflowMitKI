import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    from_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    to_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    description: Mapped[str] = mapped_column(String(255), default="")
    transfer_date: Mapped[date] = mapped_column(Date, default=lambda: date.today())
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)  # monthly, quarterly
    savings_goal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    tenant: Mapped["Tenant"] = relationship("Tenant")
    from_account: Mapped["Account"] = relationship("Account", foreign_keys=[from_account_id])
    to_account: Mapped["Account"] = relationship("Account", foreign_keys=[to_account_id])
