"""Home Sample Collection Dispatch, Routing, and Tracking API router."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.home_collection import HomeCollectionBooking
from app.models.patient import Patient
from app.models.identity import User
from app.models.core import Branch
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/home-collections", tags=["home-collections"])


class HomeCollectionCreate(BaseModel):
    branch_id: str | None = None
    patient_id: str
    appointment_date: datetime
    time_slot: str = "07:00 AM - 08:00 AM"
    address: str = Field(..., min_length=5)
    landmark: str | None = None
    pincode: str | None = None
    contact_phone: str = Field(..., min_length=10)
    alternate_phone: str | None = None
    phlebotomist_id: str | None = None
    collection_charge: float = 100.0
    notes: str | None = None


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(REQUESTED|SCHEDULED|OUT_FOR_COLLECTION|COLLECTED|ARRIVED_AT_LAB|CANCELLED)$")
    phlebotomist_id: str | None = None
    cancellation_reason: str | None = None


@router.get("")
def list_home_collections(
    status: str | None = None,
    phlebotomist_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = db.query(HomeCollectionBooking).filter(HomeCollectionBooking.tenant_id == tenant_ctx.tenant_id)
    if status:
        query = query.filter(HomeCollectionBooking.status == status.upper())
    if phlebotomist_id:
        query = query.filter(HomeCollectionBooking.phlebotomist_id == phlebotomist_id)

    records = query.order_by(HomeCollectionBooking.appointment_date.asc()).limit(limit).all()
    out = []
    for r in records:
        pat_name = f"{r.patient.first_name} {r.patient.last_name or ''}".strip() if r.patient else "Unknown"
        out.append({
            "id": r.id,
            "patient_id": r.patient_id,
            "patient_name": pat_name,
            "patient_uhid": r.patient.patient_no if r.patient else None,
            "appointment_date": r.appointment_date.isoformat(),
            "time_slot": r.time_slot,
            "address": r.address,
            "landmark": r.landmark,
            "pincode": r.pincode,
            "contact_phone": r.contact_phone,
            "alternate_phone": r.alternate_phone,
            "phlebotomist_id": r.phlebotomist_id,
            "phlebotomist_name": r.phlebotomist.name if r.phlebotomist else "Unassigned",
            "status": r.status,
            "collection_charge": float(r.collection_charge),
            "notes": r.notes,
            "collected_at": r.collected_at.isoformat() if r.collected_at else None,
            "arrived_at_lab_at": r.arrived_at_lab_at.isoformat() if r.arrived_at_lab_at else None,
        })
    return out


@router.post("", status_code=status.HTTP_201_CREATED)
def book_home_collection(
    payload: HomeCollectionCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    pat = (
        db.query(Patient)
        .filter(Patient.tenant_id == tenant_ctx.tenant_id, Patient.id == payload.patient_id)
        .first()
    )
    if not pat:
        raise HTTPException(status_code=404, detail="Patient not found")

    branch_id = payload.branch_id
    if not branch_id:
        b = db.query(Branch).filter(Branch.tenant_id == tenant_ctx.tenant_id).first()
        branch_id = b.id if b else "default-branch"

    booking = HomeCollectionBooking(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        branch_id=branch_id,
        patient_id=payload.patient_id,
        appointment_date=payload.appointment_date,
        time_slot=payload.time_slot,
        address=payload.address,
        landmark=payload.landmark,
        pincode=payload.pincode,
        contact_phone=payload.contact_phone,
        alternate_phone=payload.alternate_phone,
        phlebotomist_id=payload.phlebotomist_id,
        status="SCHEDULED" if payload.phlebotomist_id else "REQUESTED",
        collection_charge=Decimal(str(payload.collection_charge)),
        notes=payload.notes,
        created_at=datetime.utcnow(),
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {
        "id": booking.id,
        "status": booking.status,
        "appointment_date": booking.appointment_date.isoformat(),
        "time_slot": booking.time_slot,
        "message": "Home sample collection booked successfully",
    }


@router.patch("/{booking_id}/status")
def update_booking_status(
    booking_id: str,
    payload: StatusUpdate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    booking = (
        db.query(HomeCollectionBooking)
        .filter(HomeCollectionBooking.tenant_id == tenant_ctx.tenant_id, HomeCollectionBooking.id == booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = payload.status
    if payload.phlebotomist_id:
        booking.phlebotomist_id = payload.phlebotomist_id
    if payload.cancellation_reason:
        booking.cancellation_reason = payload.cancellation_reason

    now = datetime.utcnow()
    if payload.status == "COLLECTED" and not booking.collected_at:
        booking.collected_at = now
    elif payload.status == "ARRIVED_AT_LAB" and not booking.arrived_at_lab_at:
        booking.arrived_at_lab_at = now

    db.commit()
    db.refresh(booking)
    return {
        "id": booking.id,
        "status": booking.status,
        "message": f"Home collection status updated to {booking.status}",
    }


@router.get("/phlebotomists")
def list_phlebotomists(
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    users = (
        db.query(User)
        .filter(User.tenant_id == tenant_ctx.tenant_id, User.is_active == True)  # noqa: E712
        .all()
    )
    # Filter or return users suitable for field collection
    return [{"id": u.id, "name": u.name or u.username, "username": u.username} for u in users]
