"""RBAC permission catalog definitions and seeds."""

from __future__ import annotations

from typing import TypedDict


class PermissionDef(TypedDict):
    code: str
    module: str
    resource: str
    action: str
    risk_level: str


PERMISSIONS_CATALOG: list[PermissionDef] = [
    # Patient module
    {"code": "patient.view", "module": "patient", "resource": "patient", "action": "view", "risk_level": "normal"},
    {"code": "patient.create", "module": "patient", "resource": "patient", "action": "create", "risk_level": "normal"},
    {"code": "patient.edit", "module": "patient", "resource": "patient", "action": "edit", "risk_level": "normal"},
    {"code": "patient.delete", "module": "patient", "resource": "patient", "action": "delete", "risk_level": "high"},
    {"code": "patient.merge", "module": "patient", "resource": "patient", "action": "merge", "risk_level": "critical"},

    # Pathology test master permissions
    {"code": "test.view", "module": "pathology", "resource": "test", "action": "view", "risk_level": "normal"},
    {"code": "test.create", "module": "pathology", "resource": "test", "action": "create", "risk_level": "normal"},
    {"code": "test.edit", "module": "pathology", "resource": "test", "action": "edit", "risk_level": "high"},
    {"code": "test.delete", "module": "pathology", "resource": "test", "action": "delete", "risk_level": "critical"},

    # Pathology module
    {"code": "order.view", "module": "pathology", "resource": "order", "action": "view", "risk_level": "normal"},
    {"code": "order.create", "module": "pathology", "resource": "order", "action": "create", "risk_level": "normal"},
    {"code": "order.edit", "module": "pathology", "resource": "order", "action": "edit", "risk_level": "normal"},
    {"code": "order.cancel", "module": "pathology", "resource": "order", "action": "cancel", "risk_level": "high"},
    {"code": "sample.collect", "module": "pathology", "resource": "sample", "action": "collect", "risk_level": "normal"},
    {"code": "sample.receive", "module": "pathology", "resource": "sample", "action": "receive", "risk_level": "normal"},
    {"code": "sample.reject", "module": "pathology", "resource": "sample", "action": "reject", "risk_level": "high"},
    {"code": "result.view", "module": "pathology", "resource": "result", "action": "view", "risk_level": "normal"},
    {"code": "result.enter", "module": "pathology", "resource": "result", "action": "enter", "risk_level": "normal"},
    {"code": "result.edit", "module": "pathology", "resource": "result", "action": "edit", "risk_level": "high"},
    {"code": "result.verify", "module": "pathology", "resource": "result", "action": "verify", "risk_level": "high"},
    {"code": "result.approve", "module": "pathology", "resource": "result", "action": "approve", "risk_level": "critical"},

    # Reporting module
    {"code": "report.view", "module": "reporting", "resource": "report", "action": "view", "risk_level": "normal"},
    {"code": "report.print", "module": "reporting", "resource": "report", "action": "print", "risk_level": "normal"},
    {"code": "report.download", "module": "reporting", "resource": "report", "action": "download", "risk_level": "normal"},
    {"code": "report.release", "module": "reporting", "resource": "report", "action": "release", "risk_level": "critical"},
    {"code": "report.amend", "module": "reporting", "resource": "report", "action": "amend", "risk_level": "critical"},

    # Billing module
    {"code": "billing.view", "module": "billing", "resource": "invoice", "action": "view", "risk_level": "normal"},
    {"code": "billing.create", "module": "billing", "resource": "invoice", "action": "create", "risk_level": "normal"},
    {"code": "billing.discount", "module": "billing", "resource": "invoice", "action": "discount", "risk_level": "high"},
    {"code": "billing.refund", "module": "billing", "resource": "invoice", "action": "refund", "risk_level": "high"},
    {"code": "billing.cancel", "module": "billing", "resource": "invoice", "action": "cancel", "risk_level": "high"},
    {"code": "billing.payment", "module": "billing", "resource": "payment", "action": "create", "risk_level": "normal"},

    # Referral module
    {"code": "referral.view", "module": "referral", "resource": "partner", "action": "view", "risk_level": "normal"},
    {"code": "referral.rule.manage", "module": "referral", "resource": "rule", "action": "manage", "risk_level": "high"},
    {"code": "referral.commission.view", "module": "referral", "resource": "commission", "action": "view", "risk_level": "normal"},
    {"code": "referral.commission.settle", "module": "referral", "resource": "commission", "action": "settle", "risk_level": "high"},


    # Blood bank module
    {"code": "blood.donor.create", "module": "blood_bank", "resource": "donor", "action": "create", "risk_level": "normal"},
    {"code": "blood.donor.screen", "module": "blood_bank", "resource": "donor", "action": "screen", "risk_level": "high"},
    {"code": "blood.unit.receive", "module": "blood_bank", "resource": "unit", "action": "receive", "risk_level": "normal"},
    {"code": "blood.unit.release", "module": "blood_bank", "resource": "unit", "action": "release", "risk_level": "critical"},
    {"code": "blood.unit.issue", "module": "blood_bank", "resource": "unit", "action": "issue", "risk_level": "critical"},
    {"code": "blood.unit.discard", "module": "blood_bank", "resource": "unit", "action": "discard", "risk_level": "critical"},
    {"code": "blood.crossmatch.create", "module": "blood_bank", "resource": "crossmatch", "action": "create", "risk_level": "high"},
    {"code": "blood.crossmatch.approve", "module": "blood_bank", "resource": "crossmatch", "action": "approve", "risk_level": "critical"},

    # Platform module
    {"code": "user.view", "module": "platform", "resource": "user", "action": "view", "risk_level": "normal"},
    {"code": "user.create", "module": "platform", "resource": "user", "action": "create", "risk_level": "high"},
    {"code": "user.edit", "module": "platform", "resource": "user", "action": "edit", "risk_level": "high"},
    {"code": "role.manage", "module": "platform", "resource": "role", "action": "manage", "risk_level": "critical"},
    {"code": "audit.view", "module": "platform", "resource": "audit", "action": "view", "risk_level": "high"},
]


def get_all_permissions() -> list[PermissionDef]:
    return list(PERMISSIONS_CATALOG)
