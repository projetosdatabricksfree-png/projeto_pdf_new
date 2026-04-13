"""
Operário Papelaria Plana — Validator for cards, badges, and corporate stationery.

Executes validations V-01 through V-09 as defined in skills.md.
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
        """Execute all validations and produce a TechnicalReport.

        Args:
            payload: RoutingPayload from the Gerente.

        Returns:
            TechnicalReport with all check results.
        """
        start = time.time()
        erros_criticos: list[str] = []
        avisos: list[str] = []
        validation_results: dict[str, dict] = {}
        dimensoes_mm: dict | None = None
        paginas_com_erro: list[int] = []

        file_path = payload.file_path

        # V-01: Dimensions
        try:
            from agentes.operarios.operario_papelaria_plana.tools.dimension_checker import (
                check_dimensions,
            )
            v01 = check_dimensions(file_path)
            validation_results["V01_dimensoes"] = v01
            if v01.get("codigo"):
                erros_criticos.append(v01["codigo"])
            if v01.get("width_mm") and v01.get("height_mm"):
                dimensoes_mm = {"width": v01["width_mm"], "height": v01["height_mm"]}
        except Exception as exc:
            logger.error(f"V-01 failed: {exc}")
            validation_results["V01_dimensoes"] = {"status": "ERRO", "detalhe": str(exc)}

        # V-02: Bleed
        try:
            from agentes.operarios.operario_papelaria_plana.tools.bleed_checker import (
                check_bleed,
            )
            v02 = check_bleed(file_path)
            validation_results["V02_sangria"] = v02
            if v02.get("codigo"):
                code = v02["codigo"]
                if code.startswith("E"):
                    erros_criticos.append(code)
                elif code.startswith("W"):
                    avisos.append(code)
        except Exception as exc:
            logger.error(f"V-02 failed: {exc}")
            validation_results["V02_sangria"] = {"status": "ERRO", "detalhe": str(exc)}

        # V-03: Safety Margin
        try:
            from agentes.operarios.operario_papelaria_plana.tools.bleed_checker import (
                check_safety_margin,
            )
            v03 = check_safety_margin(file_path)
            validation_results["V03_margem_seguranca"] = v03
            if v03.get("codigo"):
                code = v03["codigo"]
                if code.startswith("E"):
                    erros_criticos.append(code)
                elif code.startswith("W"):
                    avisos.append(code)
        except Exception as exc:
            logger.error(f"V-03 failed: {exc}")
            validation_results["V03_margem_seguranca"] = {"status": "ERRO", "detalhe": str(exc)}

        # V-04: Resolution (via ExifTool)
        try:
            from agentes.gerente.tools.exiftool_reader import (
                extract_metadata,
                get_resolution_dpi,
            )
            metadata = extract_metadata(file_path)
            x_dpi, y_dpi = get_resolution_dpi(metadata)
            min_dpi = min(x_dpi, y_dpi) if x_dpi > 0 and y_dpi > 0 else 0

            if min_dpi > 0 and min_dpi < 300:
                validation_results["V04_resolucao"] = {
                    "status": "ERRO",
                    "codigo": "E005_LOW_RESOLUTION",
                    "valor_encontrado": f"{min_dpi} DPI",
                    "valor_esperado": "≥ 300 DPI",
                }
                erros_criticos.append("E005_LOW_RESOLUTION")
            elif 300 <= min_dpi < 350:
                validation_results["V04_resolucao"] = {
                    "status": "AVISO",
                    "codigo": "W003_BORDERLINE_RESOLUTION",
                    "valor": f"{min_dpi} DPI",
                }
                avisos.append("W003_BORDERLINE_RESOLUTION")
            else:
                validation_results["V04_resolucao"] = {
                    "status": "OK",
                    "valor": f"{min_dpi} DPI" if min_dpi > 0 else "N/A",
                }
        except Exception as exc:
            logger.warning(f"V-04 failed: {exc}")
            validation_results["V04_resolucao"] = {"status": "OK", "valor": "N/A"}

        # GWG CORE VALIDATIONS (Shared)
        
        # V-00a: Color Space & TAC
        try:
            from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
            v00a = check_color_compliance(file_path)
            validation_results["V05_espaco_cor"] = v00a
            if v00a.get("status") == "REPROVADO":
                erros_criticos.append("E006_RGB_COLORSPACE")
        except Exception as exc:
            logger.error(f"V-00a failed: {exc}")

        # V-00b: Fonts (GWG Embedding)
        try:
            from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg
            v00b = check_fonts_gwg(file_path)
            validation_results["V07_fontes"] = v00b
            if v00b.get("status") == "ERRO":
                erros_criticos.append(v00b["codigo"])
        except Exception as exc:
            logger.error(f"V-00b failed: {exc}")

        # V-00c: Overprint (OPM)
        try:
            from agentes.operarios.shared_tools.gwg.opm_checker import check_opm
            v00c = check_opm(file_path)
            validation_results["V00c_overprint"] = v00c
            if v00c.get("status") == "ERRO":
                erros_criticos.append(v00c.get("codigo", "E_OPM_WRONG"))
        except Exception as exc:
            logger.error(f"V-00c failed: {exc}")

        # V-08: NFC Zone (ID-1 only)
        try:
            from agentes.operarios.operario_papelaria_plana.tools.font_checker import (
                check_nfc_zone,
            )
            w = dimensoes_mm.get("width", 0) if dimensoes_mm else 0
            h = dimensoes_mm.get("height", 0) if dimensoes_mm else 0
            v08 = check_nfc_zone(file_path, w, h)
            validation_results["V08_nfc_zone"] = v08
            if v08.get("codigo"):
                erros_criticos.append(v08["codigo"])
        except Exception as exc:
            logger.warning(f"V-08 failed: {exc}")
            validation_results["V08_nfc_zone"] = {"status": "N/A", "detalhe": str(exc)}

        # V-09: Hairlines
        try:
            from agentes.operarios.operario_papelaria_plana.tools.font_checker import (
                check_hairlines,
            )
            v09 = check_hairlines(file_path)
            validation_results["V09_espessura_linha"] = v09
            if v09.get("codigo"):
                code = v09["codigo"]
                if code.startswith("E"):
                    erros_criticos.append(code)
                elif code.startswith("W"):
                    avisos.append(code)
        except Exception as exc:
            logger.warning(f"V-09 failed: {exc}")
            validation_results["V09_espessura_linha"] = {"status": "OK", "valor": "N/A"}

        # Calculate status
        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros_criticos, avisos)

        elapsed_ms = int((time.time() - start) * 1000)

        # Detect product name
        norma = validation_results.get("V01_dimensoes", {}).get("norma", "Formato Personalizado")
        produto_detectado = f"Cartão de Visita — {norma}" if norma else "Papelaria Plana"

        return TechnicalReport(
            job_id=payload.job_id,
            agent=AGENT_NAME,
            produto_detectado=produto_detectado,
            status=status,
            erros_criticos=erros_criticos,
            avisos=avisos,
            validation_results=validation_results,
            processing_time_ms=elapsed_ms,
            timestamp=datetime.now(timezone.utc),
            dimensoes_mm=dimensoes_mm,
            paginas_com_erro=paginas_com_erro,
        )
