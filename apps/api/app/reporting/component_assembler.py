"""Report Data Components: Reusable patient header, test table, and clinical summary assembly for report rendering."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.errors import NotFoundError
from app.models.billing import ReferralPartner
from app.models.core import Branch, Department, Tenant
from app.models.pathology import Order, OrderItem, Result, ResultValue, Sample, Test, TestReferenceRange
from app.models.patient import Patient
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


def assemble_patient_header_component(
    patient: Patient,
    order: Order,
    sample: Sample | None = None,
    referral_partner: ReferralPartner | None = None,
    branch: Branch | None = None,
) -> dict[str, Any]:
    """
    Assemble standardized patient demographic and accession context for report headers.
    """
    age_str = ""
    if patient.date_of_birth:
        now = datetime.now(timezone.utc).date()
        years = (now - patient.date_of_birth).days // 365
        age_str = f"{years} yrs"
    elif getattr(patient, "age_years", None):
        age_str = f"{patient.age_years} yrs"

    return {
        "patient_id": patient.id,
        "patient_no": patient.patient_no,
        "full_name": f"{patient.first_name} {patient.last_name or ''}".strip(),
        "first_name": patient.first_name,
        "last_name": patient.last_name or "",
        "sex": (patient.sex or "Unknown").capitalize(),
        "age": age_str or "N/A",
        "dob": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        "mobile": getattr(patient, "mobile", None) or getattr(patient, "mobile_normalized", None) or "",
        "order_id": order.id,
        "order_no": order.order_no,
        "ordered_at": order.ordered_at.isoformat() if order.ordered_at else None,
        "sample_id": sample.id if sample else None,
        "barcode": sample.barcode if sample else None,
        "specimen_type": sample.specimen_type if sample else (order.items[0].test.specimen_type if order.items and order.items[0].test else "Blood"),
        "collected_at": sample.collected_at.isoformat() if sample and sample.collected_at else None,
        "received_at": sample.received_at.isoformat() if sample and sample.received_at else None,
        "referral_partner": {
            "id": referral_partner.id if referral_partner else None,
            "name": referral_partner.name if referral_partner else "Self / Walk-in",
            "type": referral_partner.partner_type if referral_partner else "doctor",
        },
        "branch": {
            "id": branch.id if branch else None,
            "name": branch.name if branch else "Main Laboratory",
            "code": branch.code if branch else "MAIN",
        },
    }


def assemble_test_table_component(
    result: Result,
    order_item: OrderItem,
) -> dict[str, Any]:
    """
    Assemble diagnostic analytes, values, units, reference intervals, and flags for test table rendering.
    """
    t = order_item.test
    analytes_list: list[dict[str, Any]] = []

    for v in sorted(result.values, key=lambda x: x.analyte_code):
        analytes_list.append({
            "code": v.analyte_code,
            "name": v.analyte_name or (t.name if t else v.analyte_code),
            "raw_value": v.raw_value or (str(v.numeric_value) if v.numeric_value is not None else "-"),
            "numeric_value": float(v.numeric_value) if v.numeric_value is not None else None,
            "unit": v.unit or (t.unit if t else ""),
            "reference_text": v.reference_text or "Normal",
            "flag": (v.abnormal_flag or "normal").upper(),
            "is_abnormal": v.abnormal_flag not in (None, "", "normal"),
            "is_critical": v.critical_flag,
            "notes": v.notes,
        })

    return {
        "test_id": t.id if t else None,
        "test_code": t.code if t else (order_item.profile_code or "MISC"),
        "test_name": t.name if t else (order_item.profile_name or order_item.description),
        "department_name": t.department.name if t and hasattr(t, "department") and t.department else "Clinical Pathology",
        "method": t.method if t else None,
        "analytes": analytes_list,
        "status": result.status,
        "version": result.version,
    }


def assemble_report_data_context(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
) -> dict[str, Any]:
    """
    Assemble the complete multi-tenant report data context combining patient, accession, test table, and approval metadata.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    result = (
        db.query(Result)
        .options(
            joinedload(Result.values),
            joinedload(Result.order_item).joinedload(OrderItem.test),
            joinedload(Result.sample),
        )
        .filter(Result.id == result_id, Result.tenant_id == tenant_id)
        .first()
    )
    if not result:
        raise NotFoundError(f"Result '{result_id}' not found")

    order_item = result.order_item
    order = db.query(Order).filter(Order.id == order_item.order_id).first()
    if not order:
        raise NotFoundError(f"Order for result '{result_id}' not found")

    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
    if not patient:
        raise NotFoundError(f"Patient for result '{result_id}' not found")

    ref_partner = None
    if order.referral_partner_id:
        ref_partner = db.query(ReferralPartner).filter(ReferralPartner.id == order.referral_partner_id).first()

    branch = None
    if order.branch_id:
        branch = db.query(Branch).filter(Branch.id == order.branch_id).first()

    tenant_obj = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    header = assemble_patient_header_component(
        patient=patient,
        order=order,
        sample=result.sample,
        referral_partner=ref_partner,
        branch=branch,
    )
    test_table = assemble_test_table_component(result, order_item)

    return {
        "tenant": {
            "id": tenant_obj.id if tenant_obj else tenant_id,
            "name": tenant_obj.name if tenant_obj else "Diagnostic Center",
            "code": tenant_obj.code if tenant_obj else "LAB",
        },
        "patient_header": header,
        "test_table": test_table,
        "clinical_summary": {
            "result_id": result.id,
            "status": result.status,
            "version": result.version,
            "verified_at": result.verified_at.isoformat() if result.verified_at else None,
            "approved_at": result.approved_at.isoformat() if result.approved_at else None,
            "signature_hash": result.signature_hash,
            "notes": result.notes,
            "amendment_reason": result.amendment_reason,
        },
    }

