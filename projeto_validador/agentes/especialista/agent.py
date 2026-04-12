"""
Agente Especialista — Deep probing agent for ambiguous files.

Called when the Gerente's confidence is below 0.85 or ExifTool fails.
Samples at most the first 5 pages and uses PyMuPDF + Ghostscript for
structural analysis without rendering pixels.
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Faca/die-cut keywords for detection
FACA_KEYWORDS: list[str] = [
    "faca", "cutcontour", "cut contour", "cut_contour",
    "die cut", "die-cut", "diecut", "corte", "corte especial",
    "crease", "perf", "perforation",
]

SPECIALIST_TIMEOUT: int = 120  # seconds


class AgenteEspecialista:
    """Specialist agent for deep probing of ambiguous files."""

    def processar(
        self,
        file_path: str,
        metadata: dict,
    ) -> dict[str, Any]:
        """Perform deep probing and return a definitive routing decision.

        Args:
            file_path: Path to the file.
            metadata: Existing metadata from the Gerente.

        Returns:
            Dictionary with route_to, confidence, and reason.
        """
        start_time = time.time()

        probing_data: dict[str, Any] = {
            "spot_colors": [],
            "layer_names": [],
            "page_rects": [],
            "has_embedded_fonts": False,
            "raster_image_count": 0,
            "vector_path_count": 0,
            "page_count": metadata.get("page_count", 1),
        }

        # Tool 1: PyMuPDF structural analysis
        try:
            from agentes.especialista.tools.pymupdf_prober import (
                detect_spot_colors_pymupdf,
                probe_structure,
            )

            structure = probe_structure(file_path)
            probing_data.update(structure)

            spot_colors = detect_spot_colors_pymupdf(file_path)
            probing_data["spot_colors"] = spot_colors

        except Exception as exc:
            logger.warning(f"[Especialista] PyMuPDF probe failed: {exc}")

        # Tool 2: Ghostscript inspection
        try:
            from agentes.especialista.tools.gs_inspector import inspect_pdf_info

            gs_info = inspect_pdf_info(file_path)
            probing_data["layer_names"] = gs_info.get("layer_names", [])

            if gs_info.get("faca_keywords"):
                probing_data["faca_keywords"] = gs_info["faca_keywords"]

        except Exception as exc:
            logger.warning(f"[Especialista] Ghostscript probe failed: {exc}")

        # Decision logic
        decision = self._decidir(metadata, probing_data)

        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"[Especialista] Decision: {decision['route_to']} "
            f"(confidence={decision['confidence']}, "
            f"reason={decision['reason']}, "
            f"elapsed={elapsed_ms}ms)"
        )

        decision["processing_time_ms"] = elapsed_ms
        decision["probing_evidence"] = {
            "spot_colors_found": probing_data.get("spot_colors", [])[:5],
            "layer_names_found": probing_data.get("layer_names", [])[:5],
            "pages_sampled": probing_data.get("pages_sampled", 0),
        }

        return decision

    def _decidir(
        self,
        metadata: dict,
        probing_data: dict,
    ) -> dict[str, Any]:
        """Core decision logic for the specialist.

        Exactly as specified in the specialist skills.md.

        Args:
            metadata: Existing metadata.
            probing_data: Data from deep probing tools.

        Returns:
            Dictionary with route_to, confidence, and reason.
        """
        spot_colors = probing_data.get("spot_colors", [])
        layer_names = probing_data.get("layer_names", [])
        faca_keywords = probing_data.get("faca_keywords", [])
        page_rects = probing_data.get("page_rects", [])

        # Signal: Die-cut / Faca detected
        all_names = " ".join(str(s) for s in spot_colors + layer_names + faca_keywords)
        if any(k in all_names.lower() for k in FACA_KEYWORDS):
            return {
                "route_to": "operario_cortes_especiais",
                "confidence": 0.97,
                "reason": "SPOT_COLOR_FACA_DETECTED",
            }

        # Signal: Variable page widths (creep compensation = dobraduras)
        if page_rects and len(page_rects) > 1:
            widths = [r.get("width", 0) for r in page_rects]
            unique_widths = set(round(w, 1) for w in widths)
            if len(unique_widths) > 1:
                return {
                    "route_to": "operario_dobraduras",
                    "confidence": 0.91,
                    "reason": "VARIABLE_PAGE_WIDTHS_CREEP_DETECTED",
                }

        # Signal: Embedded fonts + many pages = editorial
        if probing_data.get("has_embedded_fonts") and probing_data.get("page_count", 0) > 8:
            return {
                "route_to": "operario_editoriais",
                "confidence": 0.94,
                "reason": "EMBEDDED_FONTS_MULTIPAGE",
            }

        # Signal: Pure vector, large format = CAD
        if (
            probing_data.get("raster_image_count", 0) == 0
            and probing_data.get("vector_path_count", 0) > 1000
        ):
            return {
                "route_to": "operario_projetos_cad",
                "confidence": 0.89,
                "reason": "PURE_VECTOR_LARGE_FORMAT",
            }

        # Last resort: fallback by dimension
        return self._fallback_por_dimensao(metadata)

    @staticmethod
    def _fallback_por_dimensao(metadata: dict) -> dict[str, Any]:
        """Fallback routing by dimensions when deep probing is inconclusive."""
        from agentes.gerente.agent import classificar_produto

        classify_meta = {
            "width_mm": metadata.get("width_mm", 0),
            "height_mm": metadata.get("height_mm", 0),
            "page_count": metadata.get("page_count", 1),
        }

        route_to, confidence, reason = classificar_produto(classify_meta)

        # Boost confidence slightly since we did deeper analysis
        confidence = min(confidence + 0.10, 0.95)

        return {
            "route_to": route_to if route_to != "especialista" else "operario_papelaria_plana",
            "confidence": confidence,
            "reason": f"FALLBACK_DIMENSION_{reason}",
        }
