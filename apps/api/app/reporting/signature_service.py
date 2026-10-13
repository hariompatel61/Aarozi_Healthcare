"""Signature & Stamp Service: Controlled digital signatures, pathologist stamp cards, verification, and auditability."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.reporting import DigitalSignature
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


def _check_sig_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    actor_user_id: str | None = None,
) -> None:
    user_id = actor_user_id or tenant_context.user_id
    if not user_id:
        return
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_context.tenant_id).first()
    if user and not (
        authorize_action(db, user, "result.approve", branch_id=tenant_context.branch_id)
        or authorize_action(db, user, "report.release", branch_id=tenant_context.branch_id)
        or authorize_action(db, user, "report.template.manage", branch_id=tenant_context.branch_id)
    ):
        raise ForbiddenError("User is not authorized to manage controlled digital signatures")


def register_digital_signature(
    db: Session,
    *,
    tenant_context: TenantContext,
    user_id: str,
    name: str,
    qualifications: str | None = None,
    designation: str | None = None,
    registration_no: str | None = None,
    signature_image_data: str | None = None,
    stamp_text: str | None = None,
    is_default: bool = True,
    actor_user_id: str | None = None,
) -> DigitalSignature:
    """Register or update controlled digital signature profile for a clinician/pathologist."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_sig_permission(db, tenant_context=tenant_context, actor_user_id=effective_user_id)

    target_user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not target_user:
        raise NotFoundError(f"User '{user_id}' not found in tenant")

    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Pathologist/Doctor name is required", field="name")

    existing = db.query(DigitalSignature).filter(DigitalSignature.tenant_id == tenant_id, DigitalSignature.user_id == user_id).first()
    now = datetime.now(timezone.utc)

    if existing:
        existing.name = clean_name
        existing.qualifications = qualifications.strip() if qualifications else None
        existing.designation = designation.strip() if designation else None
        existing.registration_no = registration_no.strip() if registration_no else None
        if signature_image_data:
            existing.signature_image_data = signature_image_data
        existing.stamp_text = stamp_text.strip() if stamp_text else None
        existing.is_default = is_default
        existing.status = "active"
        existing.updated_at = now
        sig = existing
        action = "digital_signature.updated"
    else:
        sig = DigitalSignature(
            tenant_id=tenant_id,
            user_id=user_id,
            name=clean_name,
            qualifications=qualifications.strip() if qualifications else None,
            designation=designation.strip() if designation else None,
            registration_no=registration_no.strip() if registration_no else None,
            signature_image_data=signature_image_data,
            stamp_text=stamp_text.strip() if stamp_text else None,
            is_default=is_default,
            status="active",
        )
        db.add(sig)
        action = "digital_signature.registered"

    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code=action,
        actor_user_id=effective_user_id,
        entity_type="digital_signature",
        entity_id=sig.id,
        after_json={
            "user_id": sig.user_id,
            "name": sig.name,
            "registration_no": sig.registration_no,
            "status": sig.status,
        },
    )

    db.commit()
    db.refresh(sig)
    return sig


def render_signature_stamp_element(
    signature: DigitalSignature,
    signed_at: datetime | None = None,
) -> dict[str, Any]:
    """
    Produce controlled signature stamp render data and HTML/SVG markup for report release.
    """
    ts_str = (signed_at or datetime.now(timezone.utc)).strftime("%d-%b-%Y %H:%M UTC")
    reg_line = f"Reg. No: {signature.registration_no}" if signature.registration_no else ""
    qual_line = signature.qualifications or ""
    desig_line = signature.designation or "Consultant Pathologist"

    img_html = f"<img src='{signature.signature_image_data}' style='max-height:35px;' alt='Signature' />" if signature.signature_image_data else f"<span style='font-family:cursive; font-size:16px; color:#1a365d;'>{signature.name}</span>"

    html_markup = (
        f'<div class="signature-stamp-block" style="display:inline-block; text-align:left; font-family:sans-serif;">\n'
        f'  <div class="sig-image" style="height:35px; margin-bottom:4px;">{img_html}</div>\n'
        f'  <div style="font-weight:bold; font-size:11px; color:#1a202c;">{signature.name}</div>\n'
        f'  <div style="font-size:9px; color:#4a5568;">{qual_line}</div>\n'
        f'  <div style="font-size:9px; color:#4a5568;">{desig_line}</div>\n'
        f'  <div style="font-size:8px; color:#718096; font-family:monospace;">{reg_line}</div>\n'
        f'  <div style="font-size:7px; color:#a0aec0; margin-top:2px;">Digitally signed &bull; {ts_str}</div>\n'
        f'</div>'
    )

    return {
        "signature_id": signature.id,
        "name": signature.name,
        "qualifications": signature.qualifications,
        "designation": signature.designation,
        "registration_no": signature.registration_no,
        "signed_at": ts_str,
        "html_markup": html_markup,
    }


def revoke_digital_signature(
    db: Session,
    *,
    tenant_context: TenantContext,
    signature_id: str,
    reason: str,
    actor_user_id: str | None = None,
) -> DigitalSignature:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_sig_permission(db, tenant_context=tenant_context, actor_user_id=effective_user_id)

    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise ValidationError("Revocation reason is required", field="reason")

    sig = db.query(DigitalSignature).filter(DigitalSignature.id == signature_id, DigitalSignature.tenant_id == tenant_id).first()
    if not sig:
        raise NotFoundError(f"Digital signature '{signature_id}' not found")

    sig.status = "revoked"
    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="digital_signature.revoked",
        actor_user_id=effective_user_id,
        entity_type="digital_signature",
        entity_id=sig.id,
        after_json={"status": "revoked", "reason": clean_reason},
    )
    db.commit()
    db.refresh(sig)
    return sig


def get_user_digital_signature(
    db: Session,
    *,
    tenant_context: TenantContext,
    user_id: str,
) -> DigitalSignature:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    sig = (
        db.query(DigitalSignature)
        .filter(
            DigitalSignature.tenant_id == tenant_context.tenant_id,
            DigitalSignature.user_id == user_id,
            DigitalSignature.status == "active",
        )
        .first()
    )
    if not sig:
        raise NotFoundError(f"No active digital signature found for user '{user_id}'")
    return sig

