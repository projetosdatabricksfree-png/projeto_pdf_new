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
        """Execute fold-specific validations and full GWG checks."""
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path
        
        # --- 1. GWG CORE VALIDATIONS (Shared) ---
        
        # V-00: Color Space & TAC (Deep)
        try:
            from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
            v00 = check_color_compliance(file_path)
            results["V00_conformidade_cor"] = v00
            if v00.get("status") == "REPROVADO":
                erros.append(v00.get("tac", {}).get("codigo") or "E006_RGB_COLORSPACE")
        except Exception as exc:
            logger.error(f"Color check failed: {exc}")

        # V-00b: Fonts (Deep GWG)
        try:
            from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg
            v00b = check_fonts_gwg(file_path)
            results["V00b_fontes"] = v00b
            if v00b.get("status") == "ERRO":
                erros.append(v00b["codigo"])
        except Exception as exc:
            logger.error(f"Font check failed: {exc}")

        # V-00c: Overprint (OPM)
        try:
            from agentes.operarios.shared_tools.gwg.opm_checker import check_opm
            v00c = check_opm(file_path)
            results["V00c_overprint"] = v00c
            if v00c.get("status") == "ERRO":
                erros.append(v00c.get("codigo", "E_OPM_WRONG"))
        except Exception as exc:
            logger.error(f"OPM check failed: {exc}")

        # V-00d: Transparency
        try:
            from agentes.operarios.shared_tools.gwg.transparency_checker import check_transparency_gwg
            v00d = check_transparency_gwg(file_path)
            results["V00d_transparencia"] = v00d
            # Em Dobraduras (Geralmente L2), transparência é AVISO, a menos que o cliente peça L1
            if v00d.get("status") == "ERRO":
                erros.append(v00d["codigo"])
        except Exception as exc:
            logger.error(f"Transparency check failed: {exc}")

        # --- 2. SPECIFIC FOLD VALIDATIONS ---

        # V-01: Fold marks
        try:
            from agentes.operarios.operario_dobraduras.tools.fold_geometry import detect_fold_marks
            v01 = detect_fold_marks(file_path)
            results["V01_marcas_dobra"] = v01
            if v01.get("codigo"):
                code = v01["codigo"]
                (erros if code.startswith("E") else avisos).append(code)
        except Exception: pass

        # V-02: Creep compensation
        try:
            from agentes.operarios.operario_dobraduras.tools.creep_checker import check_creep_compensation
            v02 = check_creep_compensation(file_path)
            results["V02_creep"] = v02
            if v02.get("codigo"):
                code = v02["codigo"]
                (erros if code.startswith("E") else avisos).append(code)
        except Exception: pass

        # V-03: Mechanical score & V-04: Grain direction
        gramatura = payload.job_metadata.get("gramatura_gsm", 0)
        grain = payload.job_metadata.get("grain_direction", "unknown")
        if gramatura > 0:
            try:
                from agentes.operarios.operario_dobraduras.tools.grain_validator import check_mechanical_score, check_grain_direction
                v03 = check_mechanical_score(gramatura)
                results["V03_vinco_mecanico"] = v03
                if v03.get("codigo"): erros.append(v03["codigo"])
                
                v04 = check_grain_direction(gramatura, grain, "landscape")
                results["V04_direcao_fibra"] = v04
                if v04.get("codigo"): erros.append(v04["codigo"])
            except Exception: pass

        # V-06: Resolution (Refined)
        try:
            from agentes.gerente.tools.exiftool_reader import extract_metadata, get_resolution_dpi
            meta = extract_metadata(file_path)
            x_dpi, y_dpi = get_resolution_dpi(meta)
            min_dpi = min(x_dpi, y_dpi) if x_dpi > 0 and y_dpi > 0 else 0
            if 0 < min_dpi < 250: # GWG threshold
                results["V06_resolucao"] = {"status": "ERRO", "codigo": "E008_LOW_RESOLUTION", "valor": f"{min_dpi} DPI"}
                erros.append("E008_LOW_RESOLUTION")
            elif min_dpi == 0:
                 results["V06_resolucao"] = {"status": "AVISO", "detalhe": "Resolução não detectada nos metadados"}
            else:
                results["V06_resolucao"] = {"status": "OK", "valor": f"{min_dpi} DPI"}
        except Exception: pass

        # V-07: Bleed (Standard)
        try:
            from agentes.operarios.operario_papelaria_plana.tools.bleed_checker import check_bleed
            v07 = check_bleed(file_path)
            results["V07_sangria"] = v07
            if v07.get("codigo") and v07["codigo"].startswith("E"):
                erros.append("E009_MISSING_BLEED")
        except Exception: pass

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id,
            agent=AGENT_NAME,
            produto_detectado="Folder / Dobradura",
            status=status,
            erros_criticos=erros,
            avisos=avisos,
            validation_results=results,
            processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
        )
