"""
ExifTool Reader — Extracts lightweight metadata from files via subprocess.

Follows Rule 5 (Subprocess Seguro):
- subprocess.run with explicit timeout
- shell=False
- Validates returncode before processing stdout
- No f-string path construction without sanitization
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Timeout for ExifTool execution (seconds)
EXIFTOOL_TIMEOUT: int = 30


def _sanitize_path(file_path: str) -> str:
    """Sanitize file path to prevent injection attacks.

    Args:
        file_path: Raw file path string.

    Returns:
        Resolved absolute path string.

    Raises:
        ValueError: If the path contains suspicious characters.
    """
    # Reject paths with shell metacharacters
    # Reject paths with shell metacharacters. 
    # Allowing () and [] as they are standard in graphics filenames 
    # and safe because we use shell=False.
    if re.search(r'[;&|`${}]', file_path):
        raise ValueError(f"Suspicious characters in file path: {file_path}")

    resolved = str(Path(file_path).resolve())
    if not Path(resolved).exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    return resolved


def extract_metadata(file_path: str) -> dict:
    """Extract metadata from a file using ExifTool.

    Uses the -fast2 flag for non-destructive reading (never opens/modifies file).

    Args:
        file_path: Path to the file to analyze.

    Returns:
        Dictionary with extracted metadata fields.

    Raises:
        RuntimeError: If ExifTool fails or times out.
    """
    safe_path = _sanitize_path(file_path)

    cmd = [
        "exiftool",
        "-json",
        "-fast2",
        "-PageCount",
        "-PDFVersion",
        "-ColorSpaceName",
        "-ImageWidth",
        "-ImageHeight",
        "-XResolution",
        "-YResolution",
        "-FileType",
        "-MIMEType",
        "-FileSize",
        safe_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            timeout=EXIFTOOL_TIMEOUT,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"ExifTool timed out after {EXIFTOOL_TIMEOUT}s for {safe_path}"
        )
    except FileNotFoundError:
        raise RuntimeError(
            "ExifTool not found. Install with: apt-get install libimage-exiftool-perl"
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"ExifTool failed (code {result.returncode}): {result.stderr.strip()}"
        )

    try:
        data = json.loads(result.stdout)
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse ExifTool output: {exc}")


def extract_dimensions_mm(metadata: dict) -> tuple[float, float]:
    """Convert metadata dimensions to millimeters.

    ExifTool reports dimensions in pixels with resolution in DPI.
    Converts to mm: dimension_mm = (pixels / dpi) * 25.4

    Args:
        metadata: Dictionary from extract_metadata().

    Returns:
        Tuple of (width_mm, height_mm).
    """
    width_px = metadata.get("ImageWidth", 0)
    height_px = metadata.get("ImageHeight", 0)
    x_res = metadata.get("XResolution", 72)
    y_res = metadata.get("YResolution", 72)

    # Default to 72 DPI if resolution is missing or zero
    x_res = x_res if x_res and x_res > 0 else 72
    y_res = y_res if y_res and y_res > 0 else 72

    width_mm = (width_px / x_res) * 25.4
    height_mm = (height_px / y_res) * 25.4

    return round(width_mm, 2), round(height_mm, 2)


def get_page_count(metadata: dict) -> int:
    """Extract page count from metadata.

    Args:
        metadata: Dictionary from extract_metadata().

    Returns:
        Number of pages (defaults to 1).
    """
    return int(metadata.get("PageCount", 1))


def get_color_space(metadata: dict) -> Optional[str]:
    """Extract color space name from metadata.

    Args:
        metadata: Dictionary from extract_metadata().

    Returns:
        Color space string or None.
    """
    return metadata.get("ColorSpaceName")


def get_resolution_dpi(metadata: dict) -> tuple[float, float]:
    """Extract resolution in DPI, handling potential string or list inputs.

    Args:
        metadata: Dictionary from extract_metadata().

    Returns:
        Tuple of (x_dpi, y_dpi).
    """
    def _parse_res(val: Any) -> float:
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            # Handle "72" or "72 dpi"
            m = re.search(r"(\d+(\.\d+)?)", val)
            return float(m.group(1)) if m else 0.0
        if isinstance(val, list) and len(val) > 0:
            return _parse_res(val[0])
        return 0.0

    x_res = _parse_res(metadata.get("XResolution"))
    y_res = _parse_res(metadata.get("YResolution"))
    return x_res, y_res


def detect_pre_routing_alerts(metadata: dict) -> list[dict]:
    """Detect pre-routing alert signals that should be logged but don't block routing.

    Args:
        metadata: Dictionary from extract_metadata().

    Returns:
        List of alert dictionaries with code and detail.
    """
    alerts: list[dict] = []

    color_space = get_color_space(metadata)
    if color_space and "rgb" in color_space.lower():
        alerts.append({
            "code": "WARN_RGB_COLORSPACE",
            "detail": f"ColorSpace={color_space}",
        })

    x_dpi, y_dpi = get_resolution_dpi(metadata)
    min_dpi = min(x_dpi, y_dpi) if x_dpi > 0 and y_dpi > 0 else 0
    if 0 < min_dpi < 300:
        alerts.append({
            "code": "WARN_LOW_RESOLUTION",
            "detail": f"DPI={min_dpi}",
        })

    pdf_version = metadata.get("PDFVersion", "")
    if pdf_version and float(pdf_version) < 1.3:
        alerts.append({
            "code": "WARN_OLD_PDF_VERSION",
            "detail": f"PDFVersion={pdf_version}",
        })

    file_size = metadata.get("FileSize", "")
    # ExifTool returns human-readable sizes like "500 MB"
    if isinstance(file_size, str) and "MB" in file_size:
        try:
            size_mb = float(file_size.replace("MB", "").strip())
            if size_mb > 500:
                alerts.append({
                    "code": "WARN_LARGE_FILE",
                    "detail": f"FileSize={file_size}",
                })
        except ValueError:
            pass

    return alerts
