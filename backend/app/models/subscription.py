"""
Subscription SQLAlchemy Model
Tracks user subscription tier and Stripe integration
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class Subscription(Base):
    """User subscription model linked to Stripe."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    # Subscription tier
    tier: Mapped[str] = mapped_column(
        Enum("free", "professional", "enterprise", name="subscription_tier"),
        default="free",
        nullable=False,
    )

    # Stripe fields
    stripe_customer_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=True
    )
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=True
    )
    stripe_price_id: Mapped[str] = mapped_column(
        String(255), nullable=True
    )

    # Status
    status: Mapped[str] = mapped_column(
        Enum("active", "canceled", "past_due", "trialing", "unpaid", name="subscription_status"),
        default="active",
        nullable=False,
    )

    # Dates
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="subscription")

    def __repr__(self) -> str:
        return f"<Subscription {self.tier} ({self.status})>"
