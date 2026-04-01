"""
Tenant ORM model
Multi-tenancy support for Cricket Analytics SaaS
"""

from sqlalchemy import String, Boolean, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from uuid import uuid4
from typing import List

from app.db.base import Base


class Tenant(Base):
    """Tenant model for multi-tenancy support"""

    __tablename__ = "tenants"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subscription_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="fan"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

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
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="tenant", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="tenant", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "subscription_tier IN ('fan', 'professional', 'enterprise')",
            name="ck_tenants_subscription_tier",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Tenant(id={self.id}, name={self.name}, tier={self.subscription_tier})>"
        )
