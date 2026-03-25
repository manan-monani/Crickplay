"""
Tenant SQLAlchemy Model
Represents an organization/team/franchise using the platform
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class Tenant(Base):
    """Tenant (organization) model for multi-tenancy."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Subdomain for routing (e.g., "teama" for teama.crickplay.com)
    subdomain: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=True
    )

    # API access
    api_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    users = relationship("User", back_populates="tenant")

    def __repr__(self) -> str:
        return f"<Tenant {self.name} ({self.slug})>"
