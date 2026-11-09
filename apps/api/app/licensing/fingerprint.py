"""Hardware Fingerprinting Engine for Aarozi Healthcare.

Generates a stable, composite hardware fingerprint for Windows, Linux, and macOS.
Binds a commercial license to a single Master Laboratory PC without relying
on unstable attributes like volatile MAC addresses or external USB dongles.

Components:
1. Motherboard / Baseboard UUID or Serial
2. CPU Processor ID / Machine Architecture
3. Primary Operating System Disk Volume Serial
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys


def _clean_str(val: str | None) -> str:
    if not val:
        return ""
    return "".join(c for c in val if c.isalnum() or c in "-_").strip()


def get_windows_hardware_ids() -> dict[str, str]:
    """Extract hardware serials on Windows using native WMIC / PowerShell queries."""
    hw = {
        "board_id": "",
        "cpu_id": "",
        "disk_id": "",
    }
    if sys.platform != "win32":
        return hw

    # 1. Motherboard UUID
    try:
        cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_ComputerSystemProduct).UUID"'
        out = subprocess.check_output(cmd, shell=True, text=True, timeout=3).strip()
        if out and "error" not in out.lower():
            hw["board_id"] = _clean_str(out)
    except Exception:
        pass

    # 2. CPU Processor ID
    try:
        cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).ProcessorId"'
        out = subprocess.check_output(cmd, shell=True, text=True, timeout=3).strip()
        if out and "error" not in out.lower():
            hw["cpu_id"] = _clean_str(out)
    except Exception:
        pass

    # 3. System Drive Serial
    try:
        cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_LogicalDisk -Filter \\"DeviceID=\'C:\'\\").VolumeSerialNumber"'
        out = subprocess.check_output(cmd, shell=True, text=True, timeout=3).strip()
        if out and "error" not in out.lower():
            hw["disk_id"] = _clean_str(out)
    except Exception:
        pass

    return hw


def get_fallback_platform_ids() -> dict[str, str]:
    """Platform-agnostic fallback for non-Windows or virtualized development."""
    return {
        "board_id": _clean_str(platform.node()),
        "cpu_id": _clean_str(f"{platform.machine()}-{platform.processor()}"),
        "disk_id": _clean_str(platform.platform()),
    }


def generate_hardware_fingerprint() -> dict[str, str]:
    """
    Computes a resilient composite hardware fingerprint.
    Returns:
        - raw_components: Dictionary of inspected identifiers
        - fingerprint_hash: SHA-256 composite hash
        - short_display_id: Formatted 16-character string for customer UI
    """
    if sys.platform == "win32":
        hw = get_windows_hardware_ids()
        # Fall back if CIM query was blocked
        if not any(hw.values()):
            hw = get_fallback_platform_ids()
    else:
        hw = get_fallback_platform_ids()

    # Create composite payload
    composite_str = f"AAROZI|{hw.get('board_id')}|{hw.get('cpu_id')}|{hw.get('disk_id')}"
    sha256_hash = hashlib.sha256(composite_str.encode("utf-8")).hexdigest()

    # Format human-readable short machine ID: HW-XXXX-XXXX-XXXX
    short_id = f"HW-{sha256_hash[:4].upper()}-{sha256_hash[4:8].upper()}-{sha256_hash[8:12].upper()}"

    return {
        "fingerprint_hash": sha256_hash,
        "short_display_id": short_id,
        "components": hw,
    }


def verify_hardware_fingerprint(expected_hash: str | None) -> bool:
    """Verifies that the current machine matches the expected license hardware hash."""
    if not expected_hash:
        # If license does not enforce hardware binding, accept
        return True
    current = generate_hardware_fingerprint()
    return current["fingerprint_hash"] == expected_hash

