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
        """Execute editorial validations."""
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        paginas_com_erro: list[int] = []
        file_path = payload.file_path
        gramatura = payload.job_metadata.get("gramatura_gsm", 90)

        # V-01: Page count
        try:
            import fitz
            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()

            if page_count % 4 != 0:
                results["V01_paginas"] = {
                    "status": "AVISO", "codigo": "W001_PAGE_COUNT_NOT_MULTIPLE_OF_4",
                    "valor": str(page_count),
                }
                avisos.append("W001_PAGE_COUNT_NOT_MULTIPLE_OF_4")
            else:
                results["V01_paginas"] = {"status": "OK", "valor": str(page_count)}
        except Exception as exc:
            results["V01_paginas"] = {"status": "ERRO", "detalhe": str(exc)}

        # V-02: Spine width
        try:
            from agentes.operarios.operario_editoriais.tools.spine_calculator import (
                check_spine_width,
            )
            results["V02_lombada"] = check_spine_width(file_path, gramatura)
        except Exception as exc:
            results["V02_lombada"] = {"status": "OK", "detalhe": str(exc)}

        # V-03: Gutter
        try:
            from agentes.operarios.operario_editoriais.tools.gutter_checker import check_gutter
            v03 = check_gutter(file_path)
            results["V03_gutter"] = v03
            if v03.get("codigo"):
                erros.append(v03["codigo"])
                paginas_com_erro.extend(v03.get("paginas", []))
        except Exception as exc:
            results["V03_gutter"] = {"status": "OK", "detalhe": str(exc)}

        # V-04: Rich Black
        try:
            from agentes.operarios.operario_editoriais.tools.richblack_detector import (
                check_rich_black,
            )
            v04 = check_rich_black(file_path)
            results["V04_rich_black"] = v04
            if v04.get("codigo"):
                erros.append(v04["codigo"])
        except Exception as exc:
            results["V04_rich_black"] = {"status": "OK", "detalhe": str(exc)}

        # V-05: Fonts (Shared GWG)
        try:
            from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg
            v05 = check_fonts_gwg(file_path)
            results["V05_fontes"] = v05
            if v05.get("status") == "ERRO":
                erros.append(v05["codigo"])
        except Exception as exc:
            logger.error(f"V-05 failed: {exc}")

        # V-06: Transparency (Shared GWG)
        try:
            from agentes.operarios.shared_tools.gwg.transparency_checker import check_transparency_gwg
            v06 = check_transparency_gwg(file_path)
            results["V06_transparencia"] = v06
            if v06.get("status") == "ERRO":
                erros.append(v06["codigo"])
            elif v06.get("status") == "AVISO":
                avisos.append(v06["codigo"])
        except Exception as exc:
            logger.error(f"V-06 failed: {exc}")

        # V-07: Color Space & TAC (Shared GWG)
        try:
            from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
            v07 = check_color_compliance(file_path)
            results["V07_cores"] = v07
            if v07.get("status") == "REPROVADO":
                erros.append("E006_RGB_COLORSPACE")
        except Exception as exc:
            logger.error(f"V-07 failed: {exc}")

        # Calculate status
        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id,
            agent=AGENT_NAME,
            produto_detectado="Publicação Editorial",
            status=status,
            erros_criticos=erros,
            avisos=avisos,
            validation_results=results,
            processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
            paginas_com_erro=paginas_com_erro,
        )
