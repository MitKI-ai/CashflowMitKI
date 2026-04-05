import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CashflowSnapshot(Base):
    __tablename__ = "cashflow_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM

    monthly_income: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_expenses: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_direct_debits: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_subscriptions: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_savings: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_net: Mapped[float] = mapped_column(Float, default=0.0)
    net_worth: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    tenant: Mapped["Tenant"] = relationship("Tenant")
