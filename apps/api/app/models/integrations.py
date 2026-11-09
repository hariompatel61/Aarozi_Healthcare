"""Integration Configuration ORM models for external SaaS and messaging providers."""
from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class IntegrationConfig(Base):
    """Multi-tenant external service configuration (WhatsApp Cloud API/Web, Google Drive, SMS, SMTP)."""
    __tablename__ = "integration_configs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # whatsapp, google_drive, sms, email
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="default")  # meta_cloud_api, direct_web, google_drive, msg91
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "category", name="uq_integration_tenant_category"),
        Index("ix_integration_configs_tenant", "tenant_id", "category"),
    )

