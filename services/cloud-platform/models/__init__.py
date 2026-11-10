"""SQLAlchemy models for Aarozi Healthcare Hosted Cloud Platform."""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class PlatformAdmin(Base):
    __tablename__ = "platform_admins"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="SUPER_ADMIN", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    billing_cycle = Column(String(50), nullable=False)
    base_price_inr = Column(Numeric(12, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    grace_days = Column(Integer, default=30, nullable=False)
    max_workstations = Column(Integer, default=10, nullable=False)
    is_lifetime = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    features_json = Column(JSONB, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TenantLaboratory(Base):
    __tablename__ = "tenant_laboratories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lab_name = Column(String(255), nullable=False)
    owner_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    gstin = Column(String(50), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False, index=True)
    plan_code = Column(String(50), ForeignKey("subscription_plans.code"), nullable=True)
    hardware_fingerprint = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    licenses = relationship("IssuedLicense", back_populates="laboratory")


class IssuedLicense(Base):
    __tablename__ = "issued_licenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    license_key = Column(String(100), unique=True, nullable=False, index=True)
    lab_id = Column(String(36), ForeignKey("tenant_laboratories.id"), nullable=False, index=True)
    plan_code = Column(String(50), ForeignKey("subscription_plans.code"), nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    grace_until = Column(DateTime, nullable=False)
    hardware_fingerprint = Column(String(255), nullable=True)
    signing_key_id = Column(String(100), default="aarozi-root-key-2026", nullable=False)
    signing_algorithm = Column(String(50), default="Ed25519", nullable=False)
    signature_hex = Column(Text, nullable=False)
    license_payload_json = Column(JSONB, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    laboratory = relationship("TenantLaboratory", back_populates="licenses")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    gateway_order_id = Column(String(100), nullable=True)
    gateway_payment_id = Column(String(100), nullable=True)
    lab_id = Column(String(36), ForeignKey("tenant_laboratories.id"), nullable=True)
    plan_code = Column(String(50), ForeignKey("subscription_plans.code"), nullable=True)
    amount_inr = Column(Numeric(12, 2), nullable=False)
    taxable_amount_inr = Column(Numeric(12, 2), nullable=False)
    gst_rate_percent = Column(Numeric(5, 2), default=18.0, nullable=False)
    gst_amount_inr = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(50), default="pending", nullable=False, index=True)
    invoice_number = Column(String(100), unique=True, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    raw_webhook_event = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DesktopRelease(Base):
    __tablename__ = "desktop_releases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(50), unique=True, nullable=False)
    release_title = Column(String(255), nullable=False)
    release_notes = Column(Text, nullable=False)
    download_url = Column(Text, nullable=False)
    file_size_mb = Column(Numeric(6, 2), nullable=False)
    sha256_checksum = Column(String(128), nullable=False)
    is_latest = Column(Boolean, default=False, nullable=False)
    is_mandatory = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CmsBlogPost(Base):
    __tablename__ = "cms_blog_posts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    excerpt = Column(Text, nullable=False)
    content_markdown = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    author_name = Column(String(100), default="Aarozi Clinical Team", nullable=False)
    read_time_minutes = Column(Integer, default=5, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False, index=True)
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
