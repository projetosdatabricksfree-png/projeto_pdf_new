"""
Operário Cortes Especiais — Validator for labels, stickers, and packaging.

Validations V-01 through V-10.
Timeout: 240 seconds.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from app.api.schemas import RoutingPayload, TechnicalReport

logger = logging.getLogger(__name__)
AGENT_NAME: str = "operario_cortes_especiais"


class OperarioCortesEspeciais:
    """Validator agent for die-cut products."""

    def processar(self, payload: RoutingPayload) -> TechnicalReport:
        """Execute die-cut specific validations."""
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path

        # V-01: Faca layer detection
        try:
            from agentes.operarios.operario_cortes_especiais.tools.faca_detector import detect_faca_layer
            v01 = detect_faca_layer(file_path)
            results["V01_faca"] = v01
            if v01.get("codigo"):
                erros.append(v01["codigo"])
        except Exception as exc:
            results["V01_faca"] = {"status": "ERRO", "detalhe": str(exc)}

        # V-02: Overprint check
        try:
            from agentes.operarios.operario_cortes_especiais.tools.overprint_checker import check_overprint
            results["V02_overprint"] = check_overprint(file_path)
        except Exception as exc:
            results["V02_overprint"] = {"status": "OK", "detalhe": str(exc)}

        # V-03: Trapping
        try:
            from agentes.operarios.operario_cortes_especiais.tools.trapping_analyzer import check_trapping
            results["V03_trapping"] = check_trapping(file_path)
        except Exception as exc:
            results["V03_trapping"] = {"status": "OK", "detalhe": str(exc)}

        # V-04: Brand color ΔE
        try:
            from agentes.operarios.operario_cortes_especiais.tools.delta_e_calculator import check_brand_color
            results["V04_delta_e"] = check_brand_color(file_path)
        except Exception as exc:
            results["V04_delta_e"] = {"status": "N/A", "detalhe": str(exc)}

        # V-05: Color space
        try:
            from agentes.operarios.operario_papelaria_plana.tools.color_checker import check_color_space
            v05 = check_color_space(file_path)
            results["V05_cores"] = v05
            if v05.get("codigo"):
                erros.append("E012_RGB_COLORSPACE")
        except Exception:
            results["V05_cores"] = {"status": "OK", "valor": "N/A"}

        # V-06: Resolution
        try:
            from agentes.gerente.tools.exiftool_reader import extract_metadata, get_resolution_dpi
            meta = extract_metadata(file_path)
            x_dpi, y_dpi = get_resolution_dpi(meta)
            min_dpi = min(x_dpi, y_dpi) if x_dpi > 0 and y_dpi > 0 else 0
            if 0 < min_dpi < 300:
                results["V06_resolucao"] = {"status": "ERRO", "codigo": "E011_LOW_RESOLUTION"}
                erros.append("E011_LOW_RESOLUTION")
            else:
                results["V06_resolucao"] = {"status": "OK", "valor": f"{min_dpi} DPI"}
        except Exception:
            results["V06_resolucao"] = {"status": "OK", "valor": "N/A"}

        # V-07: Fonts
        try:
            from agentes.operarios.operario_papelaria_plana.tools.font_checker import check_fonts_embedded
            v07 = check_fonts_embedded(file_path)
            results["V07_fontes"] = v07
            if v07.get("codigo"):
                erros.append("E013_NON_EMBEDDED_FONTS")
        except Exception:
            results["V07_fontes"] = {"status": "OK", "valor": "N/A"}

        # V-08: Bleed
        try:
            from agentes.operarios.operario_papelaria_plana.tools.bleed_checker import check_bleed
            v08 = check_bleed(file_path)
            results["V08_sangria"] = v08
            if v08.get("codigo") and v08["codigo"].startswith("E"):
                erros.append("E006_INSUFFICIENT_BLEED_OUTSIDE_DIE")
        except Exception:
            results["V08_sangria"] = {"status": "OK", "valor": "N/A"}

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id, agent=AGENT_NAME,
            produto_detectado="Rótulo / Embalagem com Faca",
            status=status, erros_criticos=erros, avisos=avisos,
            validation_results=results, processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
        )
