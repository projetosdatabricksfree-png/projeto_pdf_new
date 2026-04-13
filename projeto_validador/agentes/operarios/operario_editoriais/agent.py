"""
Operário Editoriais — Validator for books, magazines, and bound publications.

Runs the full GWG suite + editorial-specific checks (page-count multiple,
spine width, gutter).
Timeout: 300 seconds.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from app.api.schemas import RoutingPayload, TechnicalReport

logger = logging.getLogger(__name__)
AGENT_NAME: str = "operario_editoriais"


class OperarioEditoriais:
    """Validator agent for editorial publications."""

    def processar(self, payload: RoutingPayload) -> TechnicalReport:
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        paginas_com_erro: list[int] = []
        file_path = payload.file_path
        gramatura = payload.job_metadata.get("gramatura_gsm", 90)

        from agentes.operarios.shared_tools.gwg.profile_matcher import (
            get_gwg_profile, identify_profile_by_metadata,
        )
        profile_key = identify_profile_by_metadata({"produto": payload.produto_detectado or "Editorial"})
        profile = get_gwg_profile(profile_key)
        logger.info(f"[{AGENT_NAME}] Perfil dinâmico: {profile['name']}")

        # Full GWG Suite
        from agentes.operarios.shared_tools.gwg.run_full_suite import run_all_gwg_checks
        suite = run_all_gwg_checks(file_path, profile)
        for name, raw in suite["checks"].items():
            results[f"GWG_{name}"] = raw
        erros.extend(suite["erros"])
        avisos.extend(suite["avisos"])

        # V-01: Page count múltiplo de 4 (editorial)
        try:
            import fitz
            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()
            if page_count % 4 != 0:
                results["V01_paginas"] = {
                    "status": "AVISO", "codigo": "W001_PAGE_COUNT_NOT_MULTIPLE_OF_4",
                    "label": "Contagem de Páginas",
                    "found_value": f"{page_count} páginas",
                    "expected_value": "Múltiplo de 4",
                }
                avisos.append("W001_PAGE_COUNT_NOT_MULTIPLE_OF_4")
            else:
                results["V01_paginas"] = {
                    "status": "OK", "label": "Contagem de Páginas",
                    "found_value": f"{page_count} páginas",
                    "expected_value": "Múltiplo de 4",
                }
        except Exception as exc:
            results["V01_paginas"] = {"status": "AVISO", "detalhe": str(exc)}

        # V-03: Spine
        try:
            from agentes.operarios.operario_editoriais.tools.spine_calculator import check_spine_width
            results["V03_lombada"] = check_spine_width(file_path, gramatura)
        except Exception as exc:
            results["V03_lombada"] = {"status": "OK", "detalhe": str(exc)}

        # V-04: Gutter
        try:
            from agentes.operarios.operario_editoriais.tools.gutter_checker import check_gutter
            v04 = check_gutter(file_path)
            results["V04_gutter"] = v04
            if v04.get("codigo"):
                erros.append(v04["codigo"])
                paginas_com_erro.extend(v04.get("paginas", []))
        except Exception as exc:
            results["V04_gutter"] = {"status": "OK", "detalhe": str(exc)}

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id,
            agent=AGENT_NAME,
            produto_detectado=f"Editorial ({profile['name']})",
            status=status,
            erros_criticos=erros,
            avisos=avisos,
            validation_results=results,
            processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
            paginas_com_erro=paginas_com_erro,
        )
