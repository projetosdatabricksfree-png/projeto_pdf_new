"""
Ghostscript Inspector — Inspects PDF layers and spot colors via subprocess.

Follows Rule 5 (Subprocess Seguro):
- subprocess.run with explicit timeout
- shell=False
- Validates returncode
- No shell=True
"""
from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

GS_TIMEOUT: int = 60  # seconds


def _sanitize_path(file_path: str) -> str:
    """Sanitize file path for subprocess usage."""
    # Reject paths with shell metacharacters.
    # Allowing () and [] as they are standard in graphics filenames 
    # and safe because we use shell=False.
    if re.search(r'[;&|`${}]', file_path):
        raise ValueError(f"Suspicious characters in file path: {file_path}")
    resolved = str(Path(file_path).resolve())
    if not Path(resolved).exists():
        raise FileNotFoundError(f"File not found: {resolved}")
    return resolved


def inspect_pdf_info(file_path: str) -> dict[str, Any]:
    """Extract PDF info including color spaces and layers via Ghostscript.

    Uses -sDEVICE=nullpage (no output image) per Rule 1 (Anti-OOM).

    Args:
        file_path: Path to the PDF file.

    Returns:
        Dictionary with color spaces, spot colors, and layer info.
    """
    safe_path = _sanitize_path(file_path)

    cmd = [
        "gs",
        "-dBATCH",
        "-dNOPAUSE",
        "-dNODISPLAY",
        "-sDEVICE=nullpage",
        safe_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            timeout=GS_TIMEOUT,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Ghostscript timed out after {GS_TIMEOUT}s")
    except FileNotFoundError:
        raise RuntimeError("Ghostscript not found. Install with: apt-get install ghostscript")

    output = result.stdout + result.stderr

    # Parse color space info
    color_spaces: list[str] = re.findall(
        r'(ColorSpace|SpotColor|Separation|DeviceN|DeviceCMYK|DeviceRGB|DeviceGray)',
        output,
        re.IGNORECASE,
    )

    # Parse layer / OCG info
    layers: list[str] = re.findall(
        r'(Layer|OCG|Optional\s*Content)',
        output,
        re.IGNORECASE,
    )

    # Detect faca/die-cut keywords
    faca_matches: list[str] = re.findall(
        r'(faca|cutcontour|cut.contour|die.cut|vinco|crease|fold|perfil)',
        output,
        re.IGNORECASE,
    )

    # Detect RGB presence
    has_rgb = bool(re.search(r'DeviceRGB|sRGB', output, re.IGNORECASE))

    # Detect transparency
    has_transparency = bool(
        re.search(r'transparency|blend|softmask', output, re.IGNORECASE)
    )

    return {
        "color_spaces": list(set(color_spaces)),
        "layer_names": list(set(layers)),
        "faca_keywords": list(set(faca_matches)),
        "has_rgb": has_rgb,
        "has_transparency": has_transparency,
        "gs_exit_code": result.returncode,
    }


def detect_faca_layers(file_path: str) -> list[str]:
    """Specifically detect die-cut/faca layer names.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of faca-related names found.
    """
    try:
        info = inspect_pdf_info(file_path)
        return info.get("faca_keywords", [])
    except (RuntimeError, FileNotFoundError):
        return []


def check_rgb_presence(file_path: str) -> bool:
    """Check if the PDF contains RGB color spaces.

    Args:
        file_path: Path to the PDF file.

    Returns:
        True if RGB is detected.
    """
    try:
        info = inspect_pdf_info(file_path)
        return info.get("has_rgb", False)
    except (RuntimeError, FileNotFoundError):
        return False
