"""
Operário Cortes Especiais — Validator for labels, stickers, and packaging.

Runs the full GWG suite + die-cut specific checks (faca layer, trapping, ΔE,
native overprint analysis).
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
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path

        from agentes.operarios.shared_tools.gwg.profile_matcher import (
            get_gwg_profile, identify_profile_by_metadata,
        )
        profile_key = identify_profile_by_metadata({"produto": payload.produto_detectado or "Cortes Especiais"})
        profile = get_gwg_profile(profile_key)
        logger.info(f"[{AGENT_NAME}] Perfil dinâmico: {profile['name']}")

        # Full GWG Suite
        from agentes.operarios.shared_tools.gwg.run_full_suite import run_all_gwg_checks
        suite = run_all_gwg_checks(file_path, profile)
        for name, raw in suite["checks"].items():
            results[f"GWG_{name}"] = raw
        erros.extend(suite["erros"])
        avisos.extend(suite["avisos"])

        # V-01: Faca layer
        try:
            from agentes.operarios.operario_cortes_especiais.tools.faca_detector import detect_faca_layer
            v01 = detect_faca_layer(file_path)
            results["V01_faca"] = v01
            if v01.get("codigo"):
                erros.append(v01["codigo"])
        except Exception as exc:
            results["V01_faca"] = {"status": "AVISO", "detalhe": str(exc)}

        # V-02: Overprint artesanal (além do OPM checker)
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

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id, agent=AGENT_NAME,
            produto_detectado=f"Rótulo / Embalagem ({profile['name']})",
            status=status, erros_criticos=erros, avisos=avisos,
            validation_results=results, processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
        )
