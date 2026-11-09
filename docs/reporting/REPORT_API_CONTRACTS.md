# Report Engine & Template API Contracts - Aarozi Healthcare

**Author**: Senior FastAPI Backend Engineer & API Architect  
**Scope**: OpenAPI 3.1 REST contracts for Report Templates, Synthetic Preview, Approval, PDF Rendering, Digital Signatures, and Delivery.

---

## 1. Authentication & Security Policy
- All endpoints require Bearer JWT token authenticated via `app.security.auth:get_current_user`.
- Tenant context is automatically derived via `app.security.tenant_guard:get_tenant_context`.
- Permissions enforced via `app.rbac.engine:enforce_permission`.

---

## 2. API Endpoint Specification

### A. List Report Templates
- **Route**: `GET /reports/templates`
- **Permission**: `report.template.view`
- **Query Parameters**:
  - `department_id` (optional `string`)
  - `status` (optional `string`: `draft`, `active`, `archived`)
  - `limit` (default `50`, max `100`)
  - `offset` (default `0`)
- **Response**: `200 OK`
```json
[
  {
    "id": "tpl_7f9b8c12",
    "tenant_id": "ten_default_01",
    "name": "Standard Clinical Biochemistry Letterhead",
    "description": "A4 Portrait layout with NABL accreditation block",
    "is_default": true,
    "status": "active",
    "created_at": "2026-10-12T10:00:00Z"
  }
]
```

### B. Create / Update Report Template
- **Route**: `POST /reports/templates/create`
- **Permission**: `report.template.manage`
- **Status Code**: `201 Created`
- **Request Body**:
```json
{
  "name": "Pediatric CBC & Hematology Layout",
  "description": "Specialized layout displaying pediatric reference ranges and delta checks",
  "page_size": "A4",
  "orientation": "portrait",
  "margins": { "top_mm": 15, "bottom_mm": 15, "left_mm": 15, "right_mm": 15 },
  "blocks": [
    { "id": "blk_hdr", "type": "header_branding", "visible": true, "config": { "show_logo": true } },
    { "id": "blk_pt", "type": "patient_demographics", "visible": true, "config": { "compact": false } },
    { "id": "blk_res", "type": "result_table", "visible": true, "config": { "show_method": true } },
    { "id": "blk_sig", "type": "signatures_block", "visible": true, "config": { "qr_verify": true } }
  ]
}
```

### C. Live Synthetic Template Preview
- **Route**: `POST /reports/templates/{template_id}/preview`
- **Permission**: `report.template.manage`
- **Query Parameter**: `scenario` (`normal`, `abnormal_critical`, `multi_page`)
- **Response**: `200 OK` (Content-Type: `application/pdf` or Base64 JSON)
- *Security*: Rendered strictly using synthetic, mock patient fixtures. Real patient demographic or clinical data is NEVER exposed in template preview environments.

### D. Render & Retrieve Clinical PDF Report
- **Route**: `POST /reports/render/{result_id}`
- **Permission**: `report.view`
- **Request Body**:
```json
{
  "template_id": "tpl_7f9b8c12",
  "is_draft": false
}
```
- **Response**: `200 OK`
```json
{
  "report_id": "rep_9012ea8f",
  "result_id": "res_4421b8c0",
  "version_number": 1,
  "status": "released",
  "pdf_url": "/api/v1/reports/rep_9012ea8f/download",
  "sha256_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
  "released_at": "2026-10-15T14:30:00Z"
}
```

### E. Clinical Report Amendment
- **Route**: `POST /reports/{report_id}/amend`
- **Permission**: `report.amend`
- **Request Body**:
```json
{
  "amendment_reason": "Specimen re-run after 1:2 dilution for high bilirubin",
  "revised_result_values": [
    { "test_id": "test_bili_tot", "value_numeric": 21.4 }
  ]
}
```
- **Response**: `201 Created`
```json
{
  "new_report_id": "rep_9012ea90",
  "previous_report_id": "rep_9012ea8f",
  "version_number": 2,
  "status": "amended_released",
  "amendment_reason": "Specimen re-run after 1:2 dilution for high bilirubin"
}
```

### F. Multi-Channel Report Delivery
- **Route**: `POST /reports/{report_id}/deliver`
- **Permission**: `report.deliver`
- **Request Body**:
```json
{
  "channel": "whatsapp",
  "recipient": "+919876543210"
}
```
- **Response**: `200 OK` with delivery tracking ID.
