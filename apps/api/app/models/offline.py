"""Offline sync and licensing models: Devices, SyncEvents, SyncConflicts, SyncCheckpoints, LocalBackups."""

from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    device_code: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(100), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    __table_args__ = (
        Index("ix_devices_tenant_code", "tenant_id", "device_code", unique=True),
    )


class SyncEvent(Base):
    __tablename__ = "sync_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)  # INSERT, UPDATE, DELETE
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued", index=True)  # queued, batched, sent, acked, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_sync_queue", "tenant_id", "status", "created_at"),
    )


class SyncConflict(Base):
    __tablename__ = "sync_conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sync_event_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sync_events.id", ondelete="SET NULL"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")  # open, resolved_local, resolved_remote, merged
    local_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    remote_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SyncCheckpoint(Base):
    __tablename__ = "sync_checkpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    stream_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_acked_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_sync_checkpoints_tenant_device", "tenant_id", "device_id", "stream_name"),
    )


class SyncBatch(Base):
    __tablename__ = "sync_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    stream_name: Mapped[str] = mapped_column(String(100), nullable=False)
    batch_type: Mapped[str] = mapped_column(String(50), nullable=False, default="push")
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("uq_sync_batches_tenant_idempotency", "tenant_id", "idempotency_key", unique=True),
    )


class LocalBackup(Base):
    __tablename__ = "local_backups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)



class License(Base):
    __tablename__ = "licenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    license_key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    grace_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    entitlements_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    installation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    plan_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    signature_algorithm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    signing_key_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    signed_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_trusted_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    clock_rollback_detected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class OfflineActivationRequest(Base):
    __tablename__ = "offline_activation_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    installation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request_nonce: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    request_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LicenseRenewalRequest(Base):
    __tablename__ = "license_renewal_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    installation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request_nonce: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    current_license_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("licenses.id", ondelete="SET NULL"), nullable=True)
    request_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


