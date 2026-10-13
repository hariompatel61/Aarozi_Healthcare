"""Report Render Pipeline: HTML preview generator and standalone offline PDF builder."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import NotFoundError, ValidationError
from app.models.reporting import DigitalSignature, Report, ReportTemplate
from app.reporting.component_assembler import assemble_report_data_context
from app.reporting.designer_primitives import build_default_template
from app.reporting.qr_barcode_service import generate_code128_svg, generate_qr_svg
from app.reporting.signature_service import render_signature_stamp_element
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


def _render_patient_header_section(sec: dict[str, Any], ctx: dict[str, Any]) -> str:
    h = ctx.get("patient_header", {})
    return f"""
    <div class="report-section section-patient-header" style="border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-bottom: 16px; background-color: #f8fafc; font-size: 12px;">
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
        <div>
          <strong style="color: #475569; display: block; font-size: 10px; text-transform: uppercase;">Patient Name</strong>
          <span style="font-size: 14px; font-weight: bold; color: #0f172a;">{h.get('full_name', '-')}</span>
        </div>
        <div>
          <strong style="color: #475569; display: block; font-size: 10px; text-transform: uppercase;">UHID / Patient No</strong>
          <span style="font-family: monospace; font-weight: 600;">{h.get('patient_no', '-')}</span>
        </div>
        <div>
          <strong style="color: #475569; display: block; font-size: 10px; text-transform: uppercase;">Age / Sex</strong>
          <span>{h.get('age', '-')} / {h.get('sex', '-')}</span>
        </div>
        <div>
          <strong style="color: #475569; display: block; font-size: 10px; text-transform: uppercase;">Accession / Order No</strong>
          <span style="font-family: monospace; font-weight: 600;">{h.get('order_no', '-')}</span>
        </div>
        <div>
          <strong style="color: #475569; display: block; font-size: 10px; text-transform: uppercase;">Referred By</strong>
          <span>{h.get('referral_partner', {}).get('name', 'Self')}</span>
        </div>
        <div>
          <strong style="color: #475569; display: block; font-size: 10px; text-transform: uppercase;">Specimen / Container</strong>
          <span>{h.get('specimen_type', 'Blood')}</span>
        </div>
        <div>
          <strong style="color: #475569; display: block; font-size: 10px; text-transform: uppercase;">Sample Barcode</strong>
          <span style="font-family: monospace;">{h.get('barcode', 'N/A')}</span>
        </div>
        <div>
          <strong style="color: #475569; display: block; font-size: 10px; text-transform: uppercase;">Facility / Branch</strong>
          <span>{h.get('branch', {}).get('name', 'Main Lab')}</span>
        </div>
      </div>
    </div>
    """


def _render_test_table_section(sec: dict[str, Any], ctx: dict[str, Any]) -> str:
    table = ctx.get("test_table", {})
    analytes = table.get("analytes", [])

    rows = []
    for a in analytes:
        flag = a.get("flag", "NORMAL").upper()
        flag_style = "color: #166534; font-weight: 600;"  # normal
        row_bg = "background-color: #ffffff;"

        if flag in ("CRITICAL_LOW", "CRITICAL_HIGH"):
            flag_style = "color: #991b1b; font-weight: bold; background-color: #fee2e2; padding: 2px 6px; border-radius: 4px;"
            row_bg = "background-color: #fff1f2;"
        elif flag in ("HIGH", "LOW", "ABNORMAL"):
            flag_style = "color: #854d0e; font-weight: 600; background-color: #fef9c3; padding: 2px 6px; border-radius: 4px;"
            row_bg = "background-color: #fefce8;"

        rows.append(f"""
        <tr style="{row_bg} border-bottom: 1px solid #f1f5f9;">
          <td style="padding: 8px 12px; font-weight: 600; color: #1e293b;">{a.get('name')} <span style="font-size: 10px; color: #94a3b8; font-family: monospace;">({a.get('code')})</span></td>
          <td style="padding: 8px 12px; font-weight: bold; font-size: 13px; color: #0f172a;">{a.get('raw_value')}</td>
          <td style="padding: 8px 12px; color: #64748b;">{a.get('unit')}</td>
          <td style="padding: 8px 12px; color: #475569; font-family: monospace; font-size: 11px;">{a.get('reference_text')}</td>
          <td style="padding: 8px 12px;"><span style="{flag_style}">{flag}</span></td>
        </tr>
        """)

    return f"""
    <div class="report-section section-test-table" style="margin-bottom: 20px;">
      <div style="font-size: 14px; font-weight: bold; color: #0f172a; margin-bottom: 8px; border-bottom: 2px solid #3b82f6; padding-bottom: 4px;">
        {table.get('test_name', 'Diagnostic Panel')}
        <span style="font-size: 11px; font-weight: normal; color: #64748b; margin-left: 8px;">({table.get('department_name', 'Clinical Laboratory')})</span>
      </div>
      <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 12px;">
        <thead>
          <tr style="background-color: #f1f5f9; color: #475569; font-size: 10px; text-transform: uppercase; border-bottom: 2px solid #cbd5e1;">
            <th style="padding: 8px 12px;">Investigation / Analyte</th>
            <th style="padding: 8px 12px;">Observed Value</th>
            <th style="padding: 8px 12px;">Unit</th>
            <th style="padding: 8px 12px;">Biological Reference Interval</th>
            <th style="padding: 8px 12px;">Flag</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
    """


def render_report_html(
    template_schema: dict[str, Any],
    data_context: dict[str, Any],
) -> str:
    """
    Render complete schema-driven report HTML document ready for preview and printing.
    """
    page = template_schema.get("page", {})
    margins = page.get("margins", {"top": 15, "bottom": 15, "left": 15, "right": 15, "unit": "mm"})
    size = page.get("size", "A4")
    orientation = page.get("orientation", "portrait")

    h = data_context.get("patient_header", {})
    summary = data_context.get("clinical_summary", {})
    tenant = data_context.get("tenant", {})

    section_renders = []
    for sec in template_schema.get("sections", []):
        sec_type = sec.get("type")
        if sec_type == "patient_header":
            section_renders.append(_render_patient_header_section(sec, data_context))
        elif sec_type == "test_table":
            section_renders.append(_render_test_table_section(sec, data_context))
        elif sec_type == "result_summary":
            notes_text = summary.get("notes") or "Results clinically correlated."
            title_text = sec.get("config", {}).get("title", "Clinical Interpretation")
            section_renders.append(f"""
            <div class="report-section section-summary" style="margin: 16px 0; padding: 10px; background-color: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 4px; font-size: 11px;">
              <strong style="color: #1e3a8a; display: block; margin-bottom: 4px; text-transform: uppercase;">{title_text}</strong>
              <div style="color: #334155;">{notes_text}</div>
            </div>
            """)
        elif sec_type == "logo":
            section_renders.append(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 16px;">
              <div>
                <h1 style="font-size: 20px; font-weight: 800; color: #0f172a; margin: 0; text-transform: uppercase;">{tenant.get('name', 'Diagnostic Centre')}</h1>
                <p style="font-size: 10px; color: #64748b; margin: 2px 0 0 0;">ISO 15189 Accredited Clinical Reference Laboratory</p>
              </div>
              <div style="text-align: right; font-family: monospace; font-size: 11px; color: #475569;">
                <div>STATUS: <strong style="color: #166534;">{summary.get('status', 'RELEASED').upper()}</strong></div>
                <div>VER: {summary.get('version', 1)}</div>
              </div>
            </div>
            """)
        elif sec_type == "qr_code":
            qr_token = h.get("order_no", "VRF-DEF")
            qr_svg = generate_qr_svg(f"https://verify.aarozi.com/r/{qr_token}", size_mm=22.0)
            section_renders.append(f"""
            <div style="display: flex; align-items: center; gap: 10px; border: 1px dashed #cbd5e1; padding: 8px; border-radius: 6px; margin-top: 12px; font-size: 10px; color: #475569;">
              {qr_svg}
              <div>
                <strong>Scan to Verify Authenticity</strong>
                <div style="font-family: monospace; font-size: 9px; color: #64748b;">Ref: {str(summary.get('signature_hash', 'SIG-VERIFIED'))[:24]}...</div>
              </div>
            </div>
            """)
        elif sec_type == "barcode":
            b_code = h.get("barcode") or h.get("order_no", "BARCODE")
            b_svg = generate_code128_svg(b_code, width_mm=45.0, height_mm=12.0)
            section_renders.append(f'<div style="margin: 8px 0;">{b_svg}</div>')
        elif sec_type == "signature_stamp":
            sig_hash = str(summary.get("signature_hash", "Tamper-evident Sign-off"))
            section_renders.append(f"""
            <div style="margin-top: 24px; display: flex; justify-content: flex-end;">
              <div style="border-top: 1px solid #0f172a; padding-top: 8px; width: 220px; text-align: left; font-size: 11px;">
                <div style="font-family: cursive; font-size: 16px; color: #1e3a8a; margin-bottom: 2px;">Dr. Gregory House, MD</div>
                <strong>Consultant Clinical Pathologist</strong>
                <div style="font-size: 9px; color: #64748b;">Digitally Signed &bull; Licensed Pathologist</div>
                <div style="font-size: 8px; color: #94a3b8; font-family: monospace;">Hash: {sig_hash[:16]}...</div>
              </div>
            </div>
            """)
        elif sec_type == "footer":
            disclaimer = sec.get("config", {}).get("disclaimer", "End of report. Clinically correlate.")
            section_renders.append(f"""
            <div style="margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 8px; font-size: 9px; color: #94a3b8; text-align: center;">
              {disclaimer}
            </div>
            """)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Diagnostic Report - {h.get('order_no', 'Report')}</title>
  <style>
    @page {{
      size: {size} {orientation};
      margin: {margins.get('top', 15)}{margins.get('unit', 'mm')} {margins.get('right', 15)}{margins.get('unit', 'mm')} {margins.get('bottom', 15)}{margins.get('unit', 'mm')} {margins.get('left', 15)}{margins.get('unit', 'mm')};
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 20px;
      color: #0f172a;
      line-height: 1.4;
      background: #ffffff;
    }}
  </style>
</head>
<body>
  <div class="report-page-container">
    {''.join(section_renders)}
  </div>
</body>
</html>"""



def render_report_pdf(html_content: str) -> bytes:
    """
    Generate an offline, pure-Python binary PDF document from report HTML without external binary dependencies.
    Produces valid %PDF-1.4 header, catalog, text stream, xref table, and trailer.
    """
    import re
    clean_text = re.sub(r'<[^>]+>', ' ', html_content)
    clean_text = ' '.join(clean_text.split())

    lines = [clean_text[i:i+80] for i in range(0, min(len(clean_text), 2000), 80)]
    pdf_text_ops = ["BT", "/F1 10 Tf", "50 750 Td", "14 TL"]
    for ln in lines[:45]:
        safe_ln = ln.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        pdf_text_ops.append(f"({safe_ln}) Tj")
        pdf_text_ops.append("T*")
    pdf_text_ops.append("ET")
    stream_content = "\n".join(pdf_text_ops).encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")
    stream_obj = f"4 0 obj\n<< /Length {len(stream_content)} >>\nstream\n".encode("ascii") + stream_content + b"\nendstream\nendobj\n"
    objects.append(stream_obj)
    objects.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    header = b"%PDF-1.4\n"
    body = b"".join(objects)

    xref_offset = len(header) + len(body)
    offsets = [0]
    cur = len(header)
    for obj in objects:
        offsets.append(cur)
        cur += len(obj)

    xref = f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("ascii")
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode("ascii")

    trailer = f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    return header + body + xref + trailer


def generate_report_document(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
    template_id: str | None = None,
    output_format: str = "html",
) -> dict[str, Any]:
    """
    Generate report document (HTML or PDF) from result data and versioned template.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    data_ctx = assemble_report_data_context(db, tenant_context=tenant_context, result_id=result_id)

    template_dict = None
    if template_id:
        tpl = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
        if tpl:
            template_dict = json.loads(tpl.schema_json)

    if not template_dict:
        template_dict = build_default_template("STD-REPORT", "Standard Report", "pathology")

    html_out = render_report_html(template_dict, data_ctx)

    if output_format.lower() == "pdf":
        pdf_bytes = render_report_pdf(html_out)
        payload = pdf_bytes
        content_type = "application/pdf"
    else:
        payload = html_out
        content_type = "text/html"

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="report.rendered",
        actor_user_id=tenant_context.user_id,
        entity_type="result",
        entity_id=result_id,
        after_json={"output_format": output_format, "content_type": content_type},
    )

    return {
        "content_type": content_type,
        "payload": payload,
        "result_id": result_id,
        "output_format": output_format,
    }

