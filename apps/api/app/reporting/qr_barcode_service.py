"""QR and Barcode Service: Standalone, offline-capable Code128 barcode and QR verification engine."""
from __future__ import annotations

import hashlib
import uuid
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.errors import NotFoundError, ValidationError
from app.models.pathology import Result
from app.models.patient import Patient
from app.models.reporting import Report


# Standard Code 128B encoding tables (ASCII 32 to 127)
# Patterns represent widths of bars and spaces (e.g. '212222')
_CODE128_PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312", "132212", "221213",
    "221312", "231212", "112232", "122132", "122231", "113222", "123122", "123221", "223211", "221132",
    "221231", "213212", "223112", "312131", "311222", "321122", "321221", "312212", "322112", "322211",
    "212123", "212321", "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
    "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121", "313121", "211331",
    "231131", "213113", "213311", "213131", "311123", "311321", "331121", "312113", "312311", "332111",
    "314111", "221411", "431111", "111224", "111422", "121124", "121421", "141122", "141221", "112214",
    "112412", "122114", "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
    "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112", "421211", "212141",
    "214121", "412121", "111143", "111341", "131141", "114113", "114311", "411113", "411311", "113141",
    "114131", "311141", "411131", "211412", "211214", "211232", "2331112"
]
_START_B = 104
_STOP = 106


def generate_code128_svg(
    text: str,
    width_mm: float = 60.0,
    height_mm: float = 15.0,
    show_text: bool = True,
) -> str:
    """
    Generate an offline pure-SVG Code 128B barcode vector.
    """
    clean = (text or "").strip()
    if not clean:
        raise ValidationError("Cannot generate barcode for empty text", field="text")

    values = [_START_B]
    for ch in clean:
        code_val = ord(ch) - 32
        if 0 <= code_val <= 95:
            values.append(code_val)
        else:
            values.append(0)  # space fallback

    checksum = values[0]
    for i, val in enumerate(values[1:], start=1):
        checksum += i * val
    values.append(checksum % 103)
    values.append(_STOP)

    pattern_str = "".join(_CODE128_PATTERNS[v] for v in values)
    total_modules = sum(int(digit) for digit in pattern_str)

    module_width = 1.0
    view_width = total_modules * module_width
    view_height = 50.0

    rects = []
    current_x = 0.0
    for i, width_digit in enumerate(pattern_str):
        w = int(width_digit) * module_width
        if i % 2 == 0:  # Bar
            rects.append(f'<rect x="{current_x:.1f}" y="0" width="{w:.1f}" height="40" fill="black" />')
        current_x += w

    text_el = f'<text x="{view_width / 2:.1f}" y="48" text-anchor="middle" font-family="monospace" font-size="8">{clean}</text>' if show_text else ""

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_width} {view_height}" '
        f'width="{width_mm}mm" height="{height_mm}mm">\n'
        f'  <g fill="black">\n    ' + "\n    ".join(rects) + "\n  </g>\n"
        f'  {text_el}\n</svg>'
    )
    return svg


def generate_report_verification_token(
    report_id: str,
    tenant_id: str,
    report_no: str,
) -> str:
    """Generate deterministic, secure URL-safe verification token."""
    h = hashlib.sha256(f"{tenant_id}:{report_id}:{report_no}".encode("utf-8")).hexdigest()
    return f"VRF-{h[:16].upper()}"


def build_report_qr_verification_url(
    token: str,
    base_url: str = "http://localhost:3000",
) -> str:
    return f"{base_url.rstrip('/')}/verify/{token}"


def generate_qr_svg(
    url_or_token: str,
    size_mm: float = 30.0,
) -> str:
    """
    Generate an offline pure-vector SVG QR placeholder / pattern representing the verification token.
    Uses clean 21x21 matrix with finder patterns and data hashing for deterministic rendering.
    """
    h = hashlib.sha256(url_or_token.encode("utf-8")).hexdigest()
    matrix_size = 21
    scale = 5.0
    view_size = matrix_size * scale

    rects = []
    # Position detection patterns at corners (7x7 outer, 3x3 inner)
    def add_finder(ox: int, oy: int):
        for y in range(7):
            for x in range(7):
                if (
                    x == 0 or x == 6 or y == 0 or y == 6
                    or (2 <= x <= 4 and 2 <= y <= 4)
                ):
                    rects.append(f'<rect x="{(ox + x) * scale:.1f}" y="{(oy + y) * scale:.1f}" width="{scale:.1f}" height="{scale:.1f}" />')

    add_finder(0, 0)
    add_finder(14, 0)
    add_finder(0, 14)

    # Deterministic data module fill based on payload hash bits
    hash_bits = bin(int(h, 16))[2:].zfill(256)
    bit_idx = 0
    for y in range(matrix_size):
        for x in range(matrix_size):
            # Skip finders
            if (x < 8 and y < 8) or (x >= 13 and y < 8) or (x < 8 and y >= 13):
                continue
            if hash_bits[bit_idx % len(hash_bits)] == '1':
                rects.append(f'<rect x="{x * scale:.1f}" y="{y * scale:.1f}" width="{scale:.1f}" height="{scale:.1f}" />')
            bit_idx += 1

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_size:.1f} {view_size:.1f}" '
        f'width="{size_mm}mm" height="{size_mm}mm">\n'
        f'  <g fill="black">\n    ' + "\n    ".join(rects) + "\n  </g>\n"
        f'</svg>'
    )
    return svg


def verify_report_qr_token(
    db: Session,
    *,
    token: str,
) -> dict[str, Any]:
    """
    Clinically verify a report QR token, returning patient privacy-masked verification metadata.
    """
    clean_token = (token or "").strip().upper()
    if not clean_token:
        raise ValidationError("Verification token is required", field="token")

    report = (
        db.query(Report)
        .options(joinedload(Report.template))
        .filter(Report.qr_token == clean_token)
        .first()
    )
    if not report:
        raise NotFoundError(f"Verification token '{clean_token}' is invalid or expired")

    patient = db.query(Patient).filter(Patient.id == report.patient_id).first()

    # Privacy masking: e.g. "J. D." instead of full name
    initials = "Anonymous"
    if patient:
        f_init = patient.first_name[0] if patient.first_name else ""
        l_init = patient.last_name[0] if patient.last_name else ""
        initials = f"{f_init}. {l_init}.".strip()

    return {
        "verified": True,
        "is_authentic": True,
        "report_no": report.report_no,
        "status": report.status,
        "version": report.version,
        "released_at": report.released_at.isoformat() if report.released_at else None,
        "patient_initials": initials,
        "signature_hash": report.signature_hash,
        "template_name": report.template.name if report.template else "Standard Pathology Report",
    }

