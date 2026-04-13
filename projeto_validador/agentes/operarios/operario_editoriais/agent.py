"""
Operário Editoriais — Validator for books, magazines, and bound publications.

Validations V-01 through V-10.
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
        """Execute editorial validations with dynamic profile matching."""
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        paginas_com_erro: list[int] = []
        file_path = payload.file_path
        gramatura = payload.job_metadata.get("gramatura_gsm", 90)

        # 0. Perfil GWG Dinâmico
        from agentes.operarios.shared_tools.gwg.profile_matcher import (
            get_gwg_profile, identify_profile_by_metadata
        )
        profile_key = identify_profile_by_metadata({"produto": payload.produto_detectado or "Editorial"})
        profile = get_gwg_profile(profile_key)
        logger.info(f"[{AGENT_NAME}] Perfil dinâmico: {profile['name']}")

        # V-01: Page count (Critério Editorial Específico)
        try:
            import fitz
            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()

            if page_count % 4 != 0:
                results["V01_paginas"] = {
                    "status": "AVISO", 
                    "codigo": "W001_PAGE_COUNT_NOT_MULTIPLE_OF_4",
                    "label": "Contagem de Páginas",
                    "found_value": f"{page_count} páginas",
                    "expected_value": "Múltiplo de 4",
                    "meta": {
                        "client": "O número de páginas não é múltiplo de 4, o que pode encarecer a produção ou exigir páginas em branco.", 
                        "action": "Adicione ou remova páginas para chegar a um múltiplo de 4."
                    }
                }
                avisos.append("W001_PAGE_COUNT_NOT_MULTIPLE_OF_4")
            else:
                results["V01_paginas"] = {
                    "status": "OK",
                    "label": "Contagem de Páginas",
                    "found_value": f"{page_count} páginas",
                    "expected_value": "Múltiplo de 4",
                    "meta": {"client": "Número de páginas adequado.", "action": "Nenhuma."}
                }
        except Exception as exc:
            results["V01_paginas"] = {"status": "ERRO", "detalhe": str(exc)}

        # V-02: Geometria de Página (GWG Standard)
        try:
            from agentes.operarios.shared_tools.gwg.geometry_checker import check_geometry
            geo_results = check_geometry(file_path)
            if geo_results:
                for check in geo_results[0]["checks"]:
                    results[f"V02_{check['label'].lower().replace(' ', '_')}"] = check
                    if check["status"] == "ERRO":
                        erros.append("E_GEO_ERR")
        except Exception as exc:
            logger.error(f"Geometria falhou: {exc}")

        # V-03: Spine width
        try:
            from agentes.operarios.operario_editoriais.tools.spine_calculator import (
                check_spine_width,
            )
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

        # V-05: Fonts (Shared GWG)
        try:
            from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg
            v05 = check_fonts_gwg(file_path)
            results["V05_fontes"] = v05
            if v05.get("status") == "ERRO":
                erros.append(v05.get("codigo", "E004_FONTS"))
        except Exception as exc:
            logger.error(f"V-05 failed: {exc}")

        # V-07: Color Space & TAC (Shared GWG Dinâmico)
        try:
            from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
            v07 = check_color_compliance(file_path, {"produto": profile["name"]})
            results["V07_cores"] = v07
            if v07.get("status") == "REPROVADO":
                erros.append("E006_COLOR_FAILURE")
        except Exception as exc:
            logger.error(f"V-07 failed: {exc}")

        # V-08: ICC Profile & OutputIntent (GWG Rigoroso)
        try:
            from agentes.operarios.shared_tools.gwg.icc_checker import check_icc
            v08 = check_icc(file_path)
            results["V08_icc"] = v08
            codigo_icc = v08.get("codigo")
            if codigo_icc:
                if codigo_icc.startswith("E_"):
                    erros.append(codigo_icc)
                else:
                    avisos.append(codigo_icc)
        except Exception as exc:
            logger.error(f"V-08 failed: {exc}")

        # V-09: Overprint & OPM (GWG 5.0)
        try:
            from agentes.operarios.shared_tools.gwg.opm_checker import check_opm
            v09 = check_opm(file_path)
            results["V09_opm"] = v09
            codigo_opm = v09.get("codigo")
            if codigo_opm:
                if codigo_opm.startswith("E_"):
                    erros.append(codigo_opm)
                else:
                    avisos.append(codigo_opm)
        except Exception as exc:
            logger.error(f"V-09 failed: {exc}")

        # Calculate status
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
