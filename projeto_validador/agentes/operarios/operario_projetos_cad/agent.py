"""
Operário Projetos CAD — Validator for technical drawings and blueprints.

Runs the full GWG suite + CAD-specific checks (format, scale, NBR 13142
legend/binding margin).
Timeout: 180 seconds.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import fitz

from app.api.schemas import RoutingPayload, TechnicalReport

logger = logging.getLogger(__name__)
AGENT_NAME: str = "operario_projetos_cad"


class OperarioProjetosCAD:
    """Validator agent for CAD/technical drawings."""

    def processar(self, payload: RoutingPayload) -> TechnicalReport:
        start = time.time()
        erros: list[str] = []
        avisos: list[str] = []
        results: dict[str, dict] = {}
        file_path = payload.file_path
        encadernacao = payload.job_metadata.get("encadernacao", "none")

        from agentes.operarios.shared_tools.gwg.profile_matcher import (
            get_gwg_profile, identify_profile_by_metadata,
        )
        profile_key = identify_profile_by_metadata({"produto": payload.produto_detectado or "Projeto CAD"})
        profile = get_gwg_profile(profile_key)
        logger.info(f"[{AGENT_NAME}] Perfil dinâmico: {profile['name']}")

        # 1. Full GWG Suite — agora CAD também roda todos os 9 checkers
        from agentes.operarios.shared_tools.gwg.run_full_suite import run_all_gwg_checks
        suite = run_all_gwg_checks(file_path, profile, job_id=payload.job_id)
        for name, raw in suite["checks"].items():
            results[f"GWG_{name}"] = raw
        erros.extend(suite["erros"])
        avisos.extend(suite["avisos"])

        # 2. CAD-específicos — abre o documento uma única vez
        formato = None
        doc = fitz.open(file_path)
        try:
            try:
                from agentes.operarios.operario_projetos_cad.tools.scale_validator import check_format, check_scale
                v01 = check_format(doc)
                results["V01_formato"] = v01
                formato = v01.get("formato")
                if v01.get("codigo"):
                    avisos.append(v01["codigo"])

                v02 = check_scale(doc)
                results["V02_escala"] = v02
                if v02.get("codigo"):
                    erros.append(v02["codigo"])
            except Exception as exc:
                logger.warning(f"CAD format/scale: {exc}")

            try:
                from agentes.operarios.operario_projetos_cad.tools.hairline_detector import detect_hairlines
                v03 = detect_hairlines(doc)
                results["V03_hairlines_cad"] = v03
                if v03.get("codigo"):
                    erros.append(v03["codigo"])
            except Exception as exc:
                results["V03_hairlines_cad"] = {"status": "AVISO", "detalhe": str(exc)}

            try:
                from agentes.operarios.operario_projetos_cad.tools.nbr13142_checker import (
                    check_legend_area, check_binding_margin,
                )
                v04 = check_legend_area(doc, formato)
                results["V04_legenda"] = v04
                if v04.get("codigo"):
                    avisos.append(v04["codigo"])

                v05 = check_binding_margin(doc, encadernacao)
                results["V05_margem_encadernacao"] = v05
                if v05.get("codigo"):
                    erros.append(v05["codigo"])
            except Exception as exc:
                logger.warning(f"CAD NBR 13142: {exc}")
        finally:
            doc.close()

        from agentes.validador.agent import calcular_status_final
        status = calcular_status_final(erros, avisos)
        elapsed = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id, agent=AGENT_NAME,
            produto_detectado=f"Projeto Técnico {formato or 'Personalizado'} ({profile['name']})",
            status=status, erros_criticos=erros, avisos=avisos,
            validation_results=results, processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc),
        )
