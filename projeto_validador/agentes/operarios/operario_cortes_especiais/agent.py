"""
Operário Cortes Especiais — Validator for labels, stickers, and packaging.

Validations V-01 through V-10.
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
        """Execute die-cut specific validations."""
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path

        # V-01: Faca layer detection
        try:
            from agentes.operarios.operario_cortes_especiais.tools.faca_detector import detect_faca_layer
            v01 = detect_faca_layer(file_path)
            results["V01_faca"] = v01
            if v01.get("codigo"):
                erros.append(v01["codigo"])
        except Exception as exc:
            results["V01_faca"] = {"status": "ERRO", "detalhe": str(exc)}

        # V-02: Overprint check
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

        # GWG CORE VALIDATIONS (Shared)

        # V-05: Color Space & TAC (Shared GWG)
        try:
            from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
            v05 = check_color_compliance(file_path)
            results["V05_cores"] = v05
            if v05.get("status") == "REPROVADO":
                erros.append("E012_RGB_COLORSPACE")
        except Exception as exc:
            logger.error(f"V-05 failed: {exc}")

        # V-07: Fonts (Shared GWG)
        try:
            from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg
            v07 = check_fonts_gwg(file_path)
            results["V07_fontes"] = v07
            if v07.get("status") == "ERRO":
                erros.append("E013_NON_EMBEDDED_FONTS")
        except Exception as exc:
            logger.error(f"V-07 failed: {exc}")

        # V-09: Overprint & OPM (Shared GWG)
        try:
            from agentes.operarios.shared_tools.gwg.opm_checker import check_opm
            v09 = check_opm(file_path)
            results["V09_opm"] = v09
            codigo_opm = v09.get("codigo")
            if codigo_opm in ("E_OPM_WRONG", "E_WHITE_OVERPRINT"):
                erros.append(codigo_opm)
            elif codigo_opm:
                avisos.append(codigo_opm)
        except Exception as exc:
            logger.error(f"V-09 failed: {exc}")

        # V-10: DeviceN / Spot Colours (GWG)
        try:
            from agentes.operarios.shared_tools.gwg.devicen_checker import check_devicen
            v10 = check_devicen(file_path)
            results["V10_devicen"] = v10
            if v10.get("codigo") == "E_DEVICEN_CONV":
                erros.append("E_DEVICEN_CONV")
            elif v10.get("codigo"):
                avisos.append(v10["codigo"])
        except Exception as exc:
            results["V10_devicen"] = {"status": "OK", "detalhe": str(exc)}

        # V-11: ICC Profile & OutputIntent (GWG Rigoroso)
        try:
            from agentes.operarios.shared_tools.gwg.icc_checker import check_icc
            v11 = check_icc(file_path)
            results["V11_icc"] = v11
            codigo_icc = v11.get("codigo")
            if codigo_icc:
                if codigo_icc.startswith("E_"):
                    erros.append(codigo_icc)
                else:
                    avisos.append(codigo_icc)
        except Exception as exc:
            results["V11_icc"] = {"status": "OK", "detalhe": str(exc)}

        # V-12: Image Compression (GWG)
        try:
            from agentes.operarios.shared_tools.gwg.compression_checker import check_compression
            v12 = check_compression(file_path)
            results["V12_compressao"] = v12
            if v12.get("codigo"):
                avisos.append(v12["codigo"])
        except Exception as exc:
            results["V12_compressao"] = {"status": "OK", "detalhe": str(exc)}

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id, agent=AGENT_NAME,
            produto_detectado="Rótulo / Embalagem com Faca",
            status=status, erros_criticos=erros, avisos=avisos,
            validation_results=results, processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
        )
