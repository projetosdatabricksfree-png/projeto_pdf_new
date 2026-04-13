"""
Operário Papelaria Plana — Validator for cards, badges, and corporate stationery.

Executes the full GWG suite (via run_all_gwg_checks) plus domain-specific checks:
V-03 (safety margin), V-04 (dynamic resolution).
Timeout: 180 seconds.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from app.api.schemas import RoutingPayload, TechnicalReport

logger = logging.getLogger(__name__)

AGENT_NAME: str = "operario_papelaria_plana"
TIMEOUT_MS: int = 180_000


class OperarioPapelariaPlana:
    """Validator agent for small-format stationery (cards, badges)."""

    def processar(self, payload: RoutingPayload) -> TechnicalReport:
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path

        # 0. Perfil GWG Dinâmico
        from agentes.operarios.shared_tools.gwg.profile_matcher import (
            get_gwg_profile, identify_profile_by_metadata,
        )
        profile_key = identify_profile_by_metadata({"produto": payload.produto_detectado or "Papelaria Plana"})
        profile = get_gwg_profile(profile_key)
        logger.info(f"[{AGENT_NAME}] Perfil dinâmico: {profile['name']}")

        # 1. Full GWG Suite (9 checkers)
        from agentes.operarios.shared_tools.gwg.run_full_suite import run_all_gwg_checks
        suite = run_all_gwg_checks(file_path, profile, job_id=payload.job_id)
        for name, raw in suite["checks"].items():
            results[f"GWG_{name}"] = raw
        erros.extend(suite["erros"])
        avisos.extend(suite["avisos"])

        # 2. V-03 — Safety margin (domínio papelaria)
        try:
            from agentes.operarios.operario_papelaria_plana.tools.bleed_checker import (
                check_safety_margin,
            )
            v03 = check_safety_margin(file_path)
            results["V03_margem_seguranca"] = v03
            if v03.get("status") == "ERRO":
                erros.append(v03.get("codigo", "E003_SAFETY_MARGIN"))
        except Exception as exc:
            logger.error(f"V-03 failed: {exc}")

        # 3. V-04 — Resolução dinâmica baseada no perfil
        try:
            from agentes.gerente.tools.exiftool_reader import (
                extract_metadata, get_resolution_dpi,
            )
            metadata = extract_metadata(file_path)
            x_dpi, y_dpi = get_resolution_dpi(metadata)
            min_dpi = min(x_dpi, y_dpi) if x_dpi > 0 and y_dpi > 0 else 0
            min_required = profile["min_image_resolution"]
            if 0 < min_dpi < min_required:
                results["V04_resolucao"] = {
                    "status": "ERRO", "codigo": "E005_LOW_RESOLUTION",
                    "label": "Resolução de Imagem",
                    "found_value": f"{min_dpi} DPI",
                    "expected_value": f">= {min_required} DPI",
                }
                erros.append("E005_LOW_RESOLUTION")
            else:
                results["V04_resolucao"] = {
                    "status": "OK", "label": "Resolução de Imagem",
                    "found_value": f"{min_dpi} DPI" if min_dpi > 0 else "Vetorial / N/A",
                    "expected_value": f">= {min_required} DPI",
                }
        except Exception as exc:
            logger.warning(f"V-04 failed: {exc}")

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id,
            agent=AGENT_NAME,
            produto_detectado=f"{payload.produto_detectado or 'Papelaria Plana'} ({profile['name']})",
            status=status,
            erros_criticos=erros,
            avisos=avisos,
            validation_results=results,
            processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
        )
