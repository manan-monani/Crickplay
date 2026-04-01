"""
Subscription ORM model
Subscription and rate limiting for Cricket Analytics SaaS
"""

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from uuid import uuid4
from typing import Optional

from app.db.base import Base


class Subscription(Base):
    """Subscription model for tenant billing and rate limits"""

    __tablename__ = "subscriptions"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Tenant reference
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Subscription details
    tier: Mapped[str] = mapped_column(String(50), nullable=False, default="fan")
    rate_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    # Validity period
    start_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        server_default=func.current_timestamp(),
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscriptions")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "tier IN ('fan', 'professional', 'enterprise')",
            name="ck_subscriptions_tier",
        ),
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, tier={self.tier}, rate_limit={self.rate_limit})>"
