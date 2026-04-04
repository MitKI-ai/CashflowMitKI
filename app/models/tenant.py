import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    plan_tier: Mapped[str] = mapped_column(String(50), default="basic")
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    locale: Mapped[str] = mapped_column(String(10), default="de")
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="tenant")
    plans: Mapped[list["Plan"]] = relationship("Plan", back_populates="tenant")
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="tenant")
