"""
Operário Dobraduras — Validator for folders, brochures, postcards.

Validations V-01 through V-08.
Timeout: 240 seconds.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from app.api.schemas import RoutingPayload, TechnicalReport

logger = logging.getLogger(__name__)
AGENT_NAME: str = "operario_dobraduras"


class OperarioDobraduras:
    """Validator agent for folded products."""

    def processar(self, payload: RoutingPayload) -> TechnicalReport:
        """Execute fold-specific validations."""
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path
        gramatura = payload.job_metadata.get("gramatura_gsm", 0)
        grain = payload.job_metadata.get("grain_direction", "unknown")

        # V-01: Fold marks
        try:
            from agentes.operarios.operario_dobraduras.tools.fold_geometry import detect_fold_marks
            v01 = detect_fold_marks(file_path)
            results["V01_marcas_dobra"] = v01
            if v01.get("codigo"):
                code = v01["codigo"]
                (erros if code.startswith("E") else avisos).append(code)
        except Exception as exc:
            results["V01_marcas_dobra"] = {"status": "OK", "detalhe": str(exc)}

        # V-02: Creep compensation
        try:
            from agentes.operarios.operario_dobraduras.tools.creep_checker import check_creep_compensation
            v02 = check_creep_compensation(file_path)
            results["V02_creep"] = v02
            if v02.get("codigo"):
                code = v02["codigo"]
                (erros if code.startswith("E") else avisos).append(code)
        except Exception as exc:
            results["V02_creep"] = {"status": "OK", "detalhe": str(exc)}

        # V-03: Mechanical score
        if gramatura > 0:
            try:
                from agentes.operarios.operario_dobraduras.tools.grain_validator import check_mechanical_score
                v03 = check_mechanical_score(gramatura)
                results["V03_vinco_mecanico"] = v03
                if v03.get("codigo"):
                    erros.append(v03["codigo"])
            except Exception as exc:
                results["V03_vinco_mecanico"] = {"status": "OK", "detalhe": str(exc)}
        else:
            results["V03_vinco_mecanico"] = {"status": "N/A", "detalhe": "Gramatura não informada"}

        # V-04: Grain direction
        try:
            from agentes.operarios.operario_dobraduras.tools.grain_validator import check_grain_direction
            v04 = check_grain_direction(gramatura, grain, "landscape")
            results["V04_direcao_fibra"] = v04
            if v04.get("codigo"):
                erros.append(v04["codigo"])
        except Exception as exc:
            results["V04_direcao_fibra"] = {"status": "OK", "detalhe": str(exc)}

        # V-05: Color space
        try:
            from agentes.operarios.operario_papelaria_plana.tools.color_checker import check_color_space
            v05 = check_color_space(file_path)
            results["V05_cores"] = v05
            if v05.get("codigo"):
                erros.append("E007_RGB_COLORSPACE")
        except Exception:
            results["V05_cores"] = {"status": "OK", "valor": "N/A"}

        # V-06: Resolution
        try:
            from agentes.gerente.tools.exiftool_reader import extract_metadata, get_resolution_dpi
            meta = extract_metadata(file_path)
            x_dpi, y_dpi = get_resolution_dpi(meta)
            min_dpi = min(x_dpi, y_dpi) if x_dpi > 0 and y_dpi > 0 else 0
            if 0 < min_dpi < 300:
                results["V06_resolucao"] = {"status": "ERRO", "codigo": "E008_LOW_RESOLUTION"}
                erros.append("E008_LOW_RESOLUTION")
            else:
                results["V06_resolucao"] = {"status": "OK", "valor": f"{min_dpi} DPI"}
        except Exception:
            results["V06_resolucao"] = {"status": "OK", "valor": "N/A"}

        # V-07: Bleed
        try:
            from agentes.operarios.operario_papelaria_plana.tools.bleed_checker import check_bleed
            v07 = check_bleed(file_path)
            results["V07_sangria"] = v07
            if v07.get("codigo") and v07["codigo"].startswith("E"):
                erros.append("E009_MISSING_BLEED")
        except Exception:
            results["V07_sangria"] = {"status": "OK", "valor": "N/A"}

        # V-08: Fonts
        try:
            from agentes.operarios.operario_papelaria_plana.tools.font_checker import check_fonts_embedded
            v08 = check_fonts_embedded(file_path)
            results["V08_fontes"] = v08
            if v08.get("codigo"):
                erros.append("E010_NON_EMBEDDED_FONTS")
        except Exception:
            results["V08_fontes"] = {"status": "OK", "valor": "N/A"}

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id, agent=AGENT_NAME,
            produto_detectado="Folder / Dobradura",
            status=status, erros_criticos=erros, avisos=avisos,
            validation_results=results, processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
        )
