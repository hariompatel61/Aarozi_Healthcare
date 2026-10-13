"""Screening Questionnaire, Clinical Vitals Evaluation & Donor Eligibility Workflow."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.blood_bank import Donor, DonorDeferral, DonorScreening
from app.models.identity import Permission, RolePermission, UserRole
from app.security.tenant_guard import TenantContext, verify_tenant_boundary

# Canonical donor screening questions
STANDARD_QUESTIONNAIRE_QUESTIONS: list[dict[str, Any]] = [
    {
        "key": "feeling_well",
        "text": "Are you feeling well and in good health today?",
        "category": "general",
        "expected_answer": True,
        "deferral_type": "temporary",
        "deferral_days": 1,
        "reason": "Donor reported feeling unwell or acute malaise today",
    },
    {
        "key": "recent_fever_or_infection",
        "text": "Have you had a fever, cough, flu, or infection in the past 14 days?",
        "category": "general",
        "expected_answer": False,
        "deferral_type": "temporary",
        "deferral_days": 14,
        "reason": "Recent fever or active infection reported within 14 days",
    },
    {
        "key": "antibiotics_last_14_days",
        "text": "Have you taken oral or injectable antibiotics within the past 14 days?",
        "category": "medication",
        "expected_answer": False,
        "deferral_type": "temporary",
        "deferral_days": 14,
        "reason": "Antibiotic therapy completed less than 14 days ago",
    },
    {
        "key": "major_surgery_last_6_months",
        "text": "Have you undergone major surgical intervention or endoscopy in the past 6 months?",
        "category": "surgical",
        "expected_answer": False,
        "deferral_type": "temporary",
        "deferral_days": 180,
        "reason": "Major surgical intervention or endoscopic procedure within 6 months",
    },
    {
        "key": "tattoo_or_piercing_last_6_months",
        "text": "Have you had a tattoo, body piercing, or acupuncture in the past 6 months?",
        "category": "lifestyle",
        "expected_answer": False,
        "deferral_type": "temporary",
        "deferral_days": 180,
        "reason": "Tattoo or skin piercing within last 6 months (TTI window period risk)",
    },
    {
        "key": "cardiac_renal_disease",
        "text": "Do you have any history of heart disease, severe hypertension, or renal failure?",
        "category": "medical_history",
        "expected_answer": False,
        "deferral_type": "permanent",
        "deferral_days": None,
        "reason": "History of cardiovascular, renal or chronic systemic disease",
    },
    {
        "key": "high_risk_behavior",
        "text": "Have you engaged in high-risk sexual behavior or IV drug use?",
        "category": "high_risk",
        "expected_answer": False,
        "deferral_type": "permanent",
        "deferral_days": None,
        "reason": "High-risk behavior for blood-borne infectious pathogen transmission",
    },
    {
        "key": "pregnant_or_lactating",
        "text": "Are you currently pregnant or breastfeeding within the past 6 months?",
        "category": "obstetric",
        "expected_answer": False,
        "deferral_type": "temporary",
        "deferral_days": 180,
        "reason": "Pregnancy or lactation within 6 months postpartum",
    },
]


def get_screening_questionnaire_template() -> list[dict[str, Any]]:
    """Return the standard donor screening questionnaire questions."""
    return [dict(q) for q in STANDARD_QUESTIONNAIRE_QUESTIONS]


def _check_screening_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    permission_code: str = "blood.donor.screen",
    actor_user_id: str | None = None,
) -> None:
    if tenant_context.is_superuser:
        return

    effective_user_id = actor_user_id or tenant_context.user_id
    if not effective_user_id:
        raise ForbiddenError("Authenticated actor required for blood donor screening operations")

    has_perm = (
        db.query(RolePermission)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .filter(
            UserRole.user_id == effective_user_id,
            Permission.code == permission_code,
            RolePermission.allow.is_(True),
        )
        .first()
    )
    if not has_perm:
        raise ForbiddenError(f"User lacks required permission '{permission_code}'")


def evaluate_screening_vitals_and_responses(
    *,
    vitals: dict[str, Any],
    questionnaire_responses: dict[str, Any],
    donor_sex: str = "male",
) -> dict[str, Any]:
    """
    Evaluates donor physical vitals and health history questionnaire responses.
    Returns structured clinical evaluation including deferral reasons and duration.
    """
    reasons: list[str] = []
    has_permanent_deferral = False
    max_temp_days = 0

    now = datetime.now(timezone.utc)

    # 1. Physical vitals validation
    weight = vitals.get("weight_kg")
    if weight is not None:
        try:
            w_val = float(weight)
            if w_val < 45.0:
                reasons.append(f"Weight {w_val:.1f} kg below minimum requirement (45.0 kg)")
                max_temp_days = max(max_temp_days, 30)
        except (ValueError, TypeError):
            raise ValidationError("weight_kg must be a valid number", field="weight_kg")

    hb = vitals.get("hemoglobin_g_dl")
    if hb is not None:
        try:
            hb_val = float(hb)
            if hb_val < 12.5:
                reasons.append(f"Hemoglobin {hb_val:.1f} g/dL below minimum threshold (12.5 g/dL)")
                max_temp_days = max(max_temp_days, 30)
        except (ValueError, TypeError):
            raise ValidationError("hemoglobin_g_dl must be a valid number", field="hemoglobin_g_dl")

    bp_sys = vitals.get("blood_pressure_systolic")
    bp_dia = vitals.get("blood_pressure_diastolic")
    if bp_sys is not None:
        try:
            s_val = int(bp_sys)
            if s_val < 90 or s_val > 180:
                reasons.append(f"Systolic blood pressure {s_val} mmHg out of acceptable range (90-180 mmHg)")
                max_temp_days = max(max_temp_days, 1)
        except (ValueError, TypeError):
            raise ValidationError("blood_pressure_systolic must be an integer", field="blood_pressure_systolic")

    if bp_dia is not None:
        try:
            d_val = int(bp_dia)
            if d_val < 50 or d_val > 100:
                reasons.append(f"Diastolic blood pressure {d_val} mmHg out of acceptable range (50-100 mmHg)")
                max_temp_days = max(max_temp_days, 1)
        except (ValueError, TypeError):
            raise ValidationError("blood_pressure_diastolic must be an integer", field="blood_pressure_diastolic")

    pulse = vitals.get("pulse_bpm")
    if pulse is not None:
        try:
            p_val = int(pulse)
            if p_val < 50 or p_val > 100:
                reasons.append(f"Pulse rate {p_val} bpm out of acceptable range (50-100 bpm)")
                max_temp_days = max(max_temp_days, 1)
        except (ValueError, TypeError):
            raise ValidationError("pulse_bpm must be an integer", field="pulse_bpm")

    temp = vitals.get("temperature_c")
    if temp is not None:
        try:
            t_val = float(temp)
            if t_val > 37.5:
                reasons.append(f"Body temperature {t_val:.1f} °C indicates fever (> 37.5 °C)")
                max_temp_days = max(max_temp_days, 14)
        except (ValueError, TypeError):
            raise ValidationError("temperature_c must be a valid number", field="temperature_c")

    # 2. Questionnaire responses evaluation
    q_dict = {q["key"]: q for q in STANDARD_QUESTIONNAIRE_QUESTIONS}
    for key, answer in questionnaire_responses.items():
        if key not in q_dict:
            continue
        spec = q_dict[key]
        if key == "pregnant_or_lactating" and donor_sex.lower() == "male":
            continue

        if answer != spec["expected_answer"]:
            reasons.append(spec["reason"])
            if spec["deferral_type"] == "permanent":
                has_permanent_deferral = True
            elif spec["deferral_type"] == "temporary" and spec["deferral_days"]:
                max_temp_days = max(max_temp_days, spec["deferral_days"])

    if has_permanent_deferral:
        return {
            "passed": False,
            "status": "deferred_permanent",
            "eligibility_status": "ineligible",
            "deferral_reasons": reasons,
            "deferral_type": "permanent",
            "deferred_until": None,
        }

    if reasons:
        deferred_until = now + timedelta(days=max(1, max_temp_days))
        return {
            "passed": False,
            "status": "deferred_temporary",
            "eligibility_status": "ineligible",
            "deferral_reasons": reasons,
            "deferral_type": "temporary",
            "deferred_until": deferred_until,
        }

    return {
        "passed": True,
        "status": "passed",
        "eligibility_status": "eligible",
        "deferral_reasons": [],
        "deferral_type": None,
        "deferred_until": None,
    }



def _generate_screening_no(db: Session, tenant_id: str) -> str:
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"SCR-{today_str}-"
    last_screening = (
        db.query(DonorScreening)
        .filter(DonorScreening.tenant_id == tenant_id, DonorScreening.screening_no.like(f"{prefix}%"))
        .order_by(desc(DonorScreening.screening_no))
        .first()
    )
    if not last_screening:
        seq = 1
    else:
        try:
            seq = int(last_screening.screening_no.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}{seq:04d}"


def conduct_screening(
    db: Session,
    *,
    tenant_context: TenantContext,
    donor_id: str,
    weight_kg: float | None = None,
    blood_pressure_systolic: int | None = None,
    blood_pressure_diastolic: int | None = None,
    pulse_bpm: int | None = None,
    temperature_c: float | None = None,
    hemoglobin_g_dl: float | None = None,
    questionnaire_responses: dict[str, Any] | None = None,
    actor_user_id: str | None = None,
) -> DonorScreening:
    """
    Conduct clinical screening evaluation on a donor.
    Checks vitals, validates health questionnaire, records screening and updates donor deferral status.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_screening_permission(db, tenant_context=tenant_context, permission_code="blood.donor.screen", actor_user_id=effective_user_id)

    donor = db.query(Donor).filter(Donor.id == donor_id, Donor.tenant_id == tenant_id).first()
    if not donor:
        raise NotFoundError(f"Donor '{donor_id}' not found")

    if donor.status == "deferred_permanent":
        raise ConflictError(f"Donor '{donor.donor_no}' is permanently deferred and ineligible for further screening")

    vitals = {
        "weight_kg": weight_kg,
        "blood_pressure_systolic": blood_pressure_systolic,
        "blood_pressure_diastolic": blood_pressure_diastolic,
        "pulse_bpm": pulse_bpm,
        "temperature_c": temperature_c,
        "hemoglobin_g_dl": hemoglobin_g_dl,
    }
    responses = questionnaire_responses or {}

    eval_result = evaluate_screening_vitals_and_responses(
        vitals=vitals,
        questionnaire_responses=responses,
        donor_sex=donor.sex,
    )

    screening_no = _generate_screening_no(db, tenant_id)
    now = datetime.now(timezone.utc)

    deferral_id = None
    deferral_reason = "; ".join(eval_result["deferral_reasons"]) if eval_result["deferral_reasons"] else None
    deferred_until = eval_result["deferred_until"]

    if not eval_result["passed"]:
        donor.status = eval_result["status"]
        deferral = DonorDeferral(
            tenant_id=tenant_id,
            donor_id=donor.id,
            deferral_type=eval_result["deferral_type"],
            reason=deferral_reason or "Screening criteria not met",
            deferred_until=deferred_until,
            status="active",
            deferred_by=effective_user_id,
            deferred_at=now,
        )
        db.add(deferral)
        db.flush()
        deferral_id = deferral.id

    screening = DonorScreening(
        tenant_id=tenant_id,
        donor_id=donor.id,
        screening_no=screening_no,
        weight_kg=weight_kg,
        blood_pressure_systolic=blood_pressure_systolic,
        blood_pressure_diastolic=blood_pressure_diastolic,
        pulse_bpm=pulse_bpm,
        temperature_c=temperature_c,
        hemoglobin_g_dl=hemoglobin_g_dl,
        questionnaire_responses=json.dumps(responses),
        status=eval_result["status"],
        eligibility_status=eval_result["eligibility_status"],
        deferral_reason=deferral_reason,
        deferred_until=deferred_until,
        deferral_id=deferral_id,
        screened_by=effective_user_id,
        screened_at=now,
    )
    db.add(screening)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="blood.screening.conducted",
        actor_user_id=effective_user_id,
        entity_type="donor_screening",
        entity_id=screening.id,
        after_json={
            "screening_no": screening.screening_no,
            "donor_id": donor.id,
            "status": screening.status,
            "eligibility_status": screening.eligibility_status,
            "deferral_id": deferral_id,
            "reasons": eval_result["deferral_reasons"],
        },
    )

    db.commit()
    db.refresh(screening)
    return screening



def get_screening(
    db: Session,
    *,
    tenant_context: TenantContext,
    screening_id: str,
) -> DonorScreening:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    screening = (
        db.query(DonorScreening)
        .options(joinedload(DonorScreening.donor), joinedload(DonorScreening.deferral))
        .filter(DonorScreening.id == screening_id, DonorScreening.tenant_id == tenant_context.tenant_id)
        .first()
    )
    if not screening:
        raise NotFoundError(f"Screening '{screening_id}' not found")
    return screening


def list_screenings_for_donor(
    db: Session,
    *,
    tenant_context: TenantContext,
    donor_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[DonorScreening], int]:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = db.query(DonorScreening).filter(
        DonorScreening.tenant_id == tenant_context.tenant_id,
        DonorScreening.donor_id == donor_id,
    )
    total = query.count()
    items = query.order_by(desc(DonorScreening.created_at)).offset(offset).limit(limit).all()
    return items, total


def list_screenings(
    db: Session,
    *,
    tenant_context: TenantContext,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[DonorScreening], int]:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = db.query(DonorScreening).filter(DonorScreening.tenant_id == tenant_context.tenant_id)
    if status:
        query = query.filter(DonorScreening.status == status.strip().lower())

    total = query.count()
    items = query.order_by(desc(DonorScreening.created_at)).offset(offset).limit(limit).all()
    return items, total

