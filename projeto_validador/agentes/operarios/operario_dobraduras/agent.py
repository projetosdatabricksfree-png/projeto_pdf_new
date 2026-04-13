"""
Operário Dobraduras — Validator for folders, brochures, postcards.

Runs the full GWG suite + fold-specific checks (fold marks, dynamic DPI).
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
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path

        from agentes.operarios.shared_tools.gwg.profile_matcher import (
            get_gwg_profile, identify_profile_by_metadata,
        )
        profile_key = identify_profile_by_metadata({"produto": payload.produto_detectado or "Folder"})
        profile = get_gwg_profile(profile_key)
        logger.info(f"[{AGENT_NAME}] Perfil dinâmico: {profile['name']}")

        # Full GWG Suite
        from agentes.operarios.shared_tools.gwg.run_full_suite import run_all_gwg_checks
        suite = run_all_gwg_checks(file_path, profile)
        for name, raw in suite["checks"].items():
            results[f"GWG_{name}"] = raw
        erros.extend(suite["erros"])
        avisos.extend(suite["avisos"])

        # V-01: Fold marks
        try:
            from agentes.operarios.operario_dobraduras.tools.fold_geometry import detect_fold_marks
            v01 = detect_fold_marks(file_path)
            results["V01_marcas_dobra"] = v01
            if v01.get("codigo"):
                code = v01["codigo"]
                (erros if code.startswith("E") else avisos).append(code)
        except Exception as exc:
            logger.warning(f"V-01 fold marks failed: {exc}")

        # V-06: Resolução dinâmica
        try:
            from agentes.gerente.tools.exiftool_reader import extract_metadata, get_resolution_dpi
            meta = extract_metadata(file_path)
            x_dpi, y_dpi = get_resolution_dpi(meta)
            min_dpi = min(x_dpi, y_dpi) if x_dpi > 0 and y_dpi > 0 else 0
            min_required = profile["min_image_resolution"]
            if 0 < min_dpi < min_required:
                results["V06_resolucao"] = {
                    "status": "ERRO", "codigo": "E008_LOW_RESOLUTION",
                    "label": "Resolução de Imagem",
                    "found_value": f"{min_dpi} DPI",
                    "expected_value": f">= {min_required} DPI",
                }
                erros.append("E008_LOW_RESOLUTION")
            else:
                results["V06_resolucao"] = {
                    "status": "OK", "label": "Resolução de Imagem",
                    "found_value": f"{min_dpi} DPI" if min_dpi > 0 else "Vetorial / N/A",
                    "expected_value": f">= {min_required} DPI",
                }
        except Exception as exc:
            logger.warning(f"V-06 failed: {exc}")

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
