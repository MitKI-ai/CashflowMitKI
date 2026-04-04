import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RetirementProfile(Base):
    __tablename__ = "retirement_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    current_age: Mapped[int] = mapped_column(Integer, default=0)
    retirement_age: Mapped[int] = mapped_column(Integer, default=67)
    life_expectancy: Mapped[int] = mapped_column(Integer, default=85)
    desired_monthly_income: Mapped[float] = mapped_column(Float, default=0.0)
    expected_pension: Mapped[float] = mapped_column(Float, default=0.0)
    current_savings: Mapped[float] = mapped_column(Float, default=0.0)
    expected_return_pct: Mapped[float] = mapped_column(Float, default=4.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    user: Mapped["User"] = relationship("User")
