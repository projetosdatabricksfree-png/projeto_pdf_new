"""
Compression & Resolution Checker — GWG 2015 image compliance.

Inspects raster images for:
- Resolution (Effective DPI) — Dual-tier (Error/Warning) based on profile.
- Exception: Images <= 16px in either dimension are skipped (§4.26).
- JPXDecode (JPEG 2000) — E_JPEG2000 (Unsupported).
- JBIG2Decode — W_JBIG2.
- 16-bit images — W_16BIT_IMAGE.

Anti-OOM: Pixel data is NEVER loaded.
"""
from __future__ import annotations

from typing import Any
import fitz  # PyMuPDF


def check_compression(file_path: str, profile: dict | None = None) -> dict[str, Any]:
    """Inspeciona imagens para conformidade de compressão e resolução GWG2015.

    Args:
        file_path: Caminho do PDF.
        profile: Dicionário de perfil GWG (profile_matcher).
    """
    if profile is None:
        from agentes.operarios.shared_tools.gwg.profile_matcher import get_gwg_profile
        profile = get_gwg_profile("default")
    from agentes.operarios.shared_tools.gwg.rounding import gwg_round

    doc = fitz.open(file_path)
    issues: list[dict[str, Any]] = []
    images_inspected: int = 0
    dpi_values: list[float] = []

    # Thresholds from profile
    min_err = profile.get("min_image_resolution", 150)
    min_warn = profile.get("warn_image_resolution", 225)

    try:
        # We iterate page-by-page to accurately determine Effective DPI (instances)
        for page_num in range(doc.page_count):
            page = doc[page_num]
            # xrefs=True gives us the xref for each image instance on the page
            img_infos = page.get_image_info(xrefs=True)
            
            for info in img_infos:
                images_inspected += 1
                xref = info.get("xref")
                if not xref:
                    continue

                width_px = info["width"]
                height_px = info["height"]
                bbox = info["bbox"]  # [x0, y0, x1, y1] in points

                # --- 16px Exception (§4.26) ---
                if width_px <= 16 or height_px <= 16:
                    continue

                # --- Effective DPI Calculation ---
                bbox_w = abs(bbox[2] - bbox[0])
                bbox_h = abs(bbox[3] - bbox[1])
                
                if bbox_w > 0 and bbox_h > 0:
                    dpi_x = width_px / (bbox_w / 72.0)
                    dpi_y = height_px / (bbox_h / 72.0)
                    effective_dpi = min(dpi_x, dpi_y)
                    dpi_values.append(effective_dpi)

                    # §3.15 rounding — image precision = 0 decimals (HALF_UP)
                    effective_dpi_rounded = gwg_round(effective_dpi, kind="image")

                    # Resolution Validation (Dual-Tier)
                    if effective_dpi_rounded < min_err:
                        issues.append({
                            "xref": xref,
                            "page": page_num + 1,
                            "codigo": "E_LOW_RESOLUTION_CRITICAL",
                            "severity": "ERRO",
                            "found_value": f"{round(effective_dpi, 1)} DPI",
                            "expected_value": f"≥ {min_err} DPI",
                            "meta": {"dim": f"{width_px}x{height_px}px"}
                        })
                    elif effective_dpi_rounded < min_warn:
                        issues.append({
                            "xref": xref,
                            "page": page_num + 1,
                            "codigo": "W_LOW_RESOLUTION_MARGINAL",
                            "severity": "AVISO",
                            "found_value": f"{round(effective_dpi, 1)} DPI",
                            "expected_value": f"≥ {min_warn} DPI",
                            "meta": {"dim": f"{width_px}x{height_px}px"}
                        })

                # --- Metadata-based checks (Filters & BPC) ---
                # These attributes are global to the image object (XREF)
                try:
                    obj_dict = doc.xref_dict(xref)
                    
                    # 16-bit depth
                    if "/BitsPerComponent 16" in obj_dict:
                        issues.append({
                            "xref": xref,
                            "page": page_num + 1,
                            "codigo": "W_16BIT_IMAGE",
                            "severity": "AVISO"
                        })

                    # Forbidden filters
                    if "/Filter" in obj_dict:
                        if "/JPXDecode" in obj_dict:
                            issues.append({
                                "xref": xref,
                                "page": page_num + 1,
                                "codigo": "E_JPEG2000",
                                "severity": "ERRO",
                                "found_value": "JPEG 2000",
                                "expected_value": "DCT/Flate"
                            })
                        if "/JBIG2Decode" in obj_dict:
                            issues.append({
                                "xref": xref,
                                "page": page_num + 1,
                                "codigo": "W_JBIG2",
                                "severity": "AVISO"
                            })
                except Exception:
                    pass

        min_dpi_overall = round(min(dpi_values), 1) if dpi_values else None
        max_dpi_overall = round(max(dpi_values), 1) if dpi_values else None

        if not issues:
            return {
                "status": "OK",
                "images_inspected": images_inspected,
                "min_dpi": min_dpi_overall,
                "max_dpi": max_dpi_overall,
            }

        # Select primary issue (ERROR takes priority)
        has_errors = any(i["severity"] == "ERRO" for i in issues)
        primary = next((i for i in issues if i["severity"] == "ERRO"), issues[0])

        return {
            "status": "ERRO" if has_errors else "AVISO",
            "codigo": primary["codigo"],
            "label": "Resolução e Compressão",
            "found_value": primary.get("found_value", "Incerto"),
            "expected_value": primary.get("expected_value", "N/A"),
            "issues": issues,
            "images_inspected": images_inspected,
            "min_dpi": min_dpi_overall,
            "max_dpi": max_dpi_overall
        }

    finally:
        doc.close()
