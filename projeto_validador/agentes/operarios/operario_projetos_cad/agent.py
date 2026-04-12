"""
Operário Projetos CAD — Validator for technical drawings and blueprints.

Validations V-01 through V-09.
Timeout: 180 seconds.
"""
from __future__ import annotations

import logging
import time
import fitz
from datetime import datetime, timezone

from app.api.schemas import RoutingPayload, TechnicalReport

logger = logging.getLogger(__name__)
AGENT_NAME: str = "operario_projetos_cad"


class OperarioProjetosCAD:
    """Validator agent for CAD/technical drawings."""

    def processar(self, payload: RoutingPayload) -> TechnicalReport:
        """Execute CAD-specific validations."""
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path
        encadernacao = payload.job_metadata.get("encadernacao", "none")

        # Open document once for all tools
        doc = fitz.open(file_path)
        
        try:
            # V-01: Format/dimensions
            try:
                from agentes.operarios.operario_projetos_cad.tools.scale_validator import check_format
                v01 = check_format(doc)
                results["V01_formato"] = v01
                formato = v01.get("formato")
                if v01.get("codigo"):
                    avisos.append(v01["codigo"])
            except Exception as exc:
                results["V01_formato"] = {"status": "OK", "detalhe": str(exc)}
                formato = None

            # V-02: Scale 1:1
            try:
                from agentes.operarios.operario_projetos_cad.tools.scale_validator import check_scale
                v02 = check_scale(doc)
                results["V02_escala"] = v02
                if v02.get("codigo"):
                    erros.append(v02["codigo"])
            except Exception as exc:
                results["V02_escala"] = {"status": "OK", "detalhe": str(exc)}

            # V-03: Hairlines (Using Process Isolation)
            try:
                from agentes.operarios.operario_projetos_cad.tools.hairline_detector import detect_hairlines
                v03 = detect_hairlines(doc)
                results["V03_hairlines"] = v03
                if v03.get("codigo"):
                    erros.append(v03["codigo"])
            except Exception as exc:
                # This should be caught inside detect_hairlines, but as a secondary safety:
                results["V03_hairlines"] = {"status": "AVISO", "detalhe": f"Falha na detecção: {str(exc)}"}

            # V-04: NBR 13142 legend area
            try:
                from agentes.operarios.operario_projetos_cad.tools.nbr13142_checker import check_legend_area
                v04 = check_legend_area(doc, formato)
                results["V04_legenda"] = v04
                if v04.get("codigo"):
                    avisos.append(v04["codigo"])
            except Exception as exc:
                results["V04_legenda"] = {"status": "N/A", "detalhe": str(exc)}

            # V-05: Binding margin
            try:
                from agentes.operarios.operario_projetos_cad.tools.nbr13142_checker import check_binding_margin
                v05 = check_binding_margin(doc, encadernacao)
                results["V05_margem_encadernacao"] = v05
                if v05.get("codigo"):
                    erros.append(v05["codigo"])
            except Exception as exc:
                results["V05_margem_encadernacao"] = {"status": "N/A", "detalhe": str(exc)}

            # V-06: Color space (Shared tool - uses file_path internaly or GS)
            try:
                from agentes.operarios.operario_papelaria_plana.tools.color_checker import check_color_space
                v06 = check_color_space(file_path)
                results["V06_cores"] = v06
                if v06.get("codigo"):
                    erros.append("E004_RGB_COLORSPACE")
            except Exception:
                results["V06_cores"] = {"status": "OK", "valor": "N/A"}

            # V-07: Fonts (Shared tool)
            try:
                from agentes.operarios.operario_papelaria_plana.tools.font_checker import check_fonts_embedded
                v07 = check_fonts_embedded(file_path)
                results["V07_fontes"] = v07
            except Exception:
                results["V07_fontes"] = {"status": "OK", "valor": "N/A"}

        finally:
            doc.close()

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id, agent=AGENT_NAME,
            produto_detectado=f"Projeto Técnico {formato or 'Personalizado'}",
            status=status, erros_criticos=erros, avisos=avisos,
            validation_results=results, processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
        )
