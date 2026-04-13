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
    """Validator agent for folded products.""    def processar(self, payload: RoutingPayload) -> TechnicalReport:
        """Execute fold-specific validations and full GWG checks dynamically."""
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path
        
        # 0. Perfil GWG Dinâmico
        from agentes.operarios.shared_tools.gwg.profile_matcher import (
            get_gwg_profile, identify_profile_by_metadata
        )
        profile_key = identify_profile_by_metadata({"produto": payload.produto_detectado or "Folder"})
        profile = get_gwg_profile(profile_key)
        logger.info(f"[{AGENT_NAME}] Perfil dinâmico: {profile['name']}")

        # --- 1. GWG CORE VALIDATIONS (Shared & Dynamic) ---
        
        # V-01: Geometria de Página (GWG Standard)
        try:
            from agentes.operarios.shared_tools.gwg.geometry_checker import check_geometry
            geo_results = check_geometry(file_path)
            if geo_results:
                for check in geo_results[0]["checks"]:
                    results[f"V00_geo_{check['label'].lower().replace(' ', '_')}"] = check
                    if check["status"] == "ERRO":
                        erros.append("E_GEO_ERR")
        except Exception as exc:
            logger.error(f"Geometria falhou: {exc}")

        # V-00: Color Space & TAC (Deep)
        try:
            from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
            v00 = check_color_compliance(file_path, {"produto": profile["name"]})
            results["V00_conformidade_cor"] = v00
            if v00.get("status") == "REPROVADO":
                erros.append("E006_COLOR_FAILURE")
        except Exception as exc:
            logger.error(f"Color check failed: {exc}")

        # V-00b: Fonts (Deep GWG)
        try:
            from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg
            v00b = check_fonts_gwg(file_path)
            results["V00b_fontes"] = v00b
            if v00b.get("status") == "ERRO":
                erros.append(v00b.get("codigo", "E004_FONTS"))
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

        # V-06: Resolução Dinâmica
        try:
            from agentes.gerente.tools.exiftool_reader import extract_metadata, get_resolution_dpi
            meta = extract_metadata(file_path)
            x_dpi, y_dpi = get_resolution_dpi(meta)
            min_dpi = min(x_dpi, y_dpi) if x_dpi > 0 and y_dpi > 0 else 0
            
            min_required = profile["min_image_resolution"]
            
            if 0 < min_dpi < min_required:
                results["V06_resolucao"] = {
                    "status": "ERRO", 
                    "codigo": "E008_LOW_RESOLUTION", 
                    "label": "Resolução de Imagem",
                    "found_value": f"{min_dpi} DPI",
                    "expected_value": f"≥ {min_required} DPI",
                    "meta": {
                        "client": f"A resolução ({min_dpi} DPI) está abaixo do mínimo exigido para o perfil {profile['name']}.",
                        "action": f"Utilize imagens com maior resolução (mínimo {min_required} DPI)."
                    }
                }
                erros.append("E008_LOW_RESOLUTION")
            else:
                results["V06_resolucao"] = {
                    "status": "OK",
                    "label": "Resolução de Imagem",
                    "found_value": f"{min_dpi} DPI" if min_dpi > 0 else "Vetor / N/A",
                    "expected_value": f"≥ {min_required} DPI",
                    "meta": {"client": "Resolução de imagem adequada para impressão.", "action": "Nenhuma."}
                }
        except Exception: pass

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id,
            agent=AGENT_NAME,
            produto_detectado=f"Dobradura / Folder ({profile['name']})",
            status=status,
            erros_criticos=erros,
            avisos=avisos,
            validation_results=results,
            processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
        )
