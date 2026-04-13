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
    """Validator agent for small-format stationery (cards, badges).""    def processar(self, payload: RoutingPayload) -> TechnicalReport:
        """Execute all validations and produce a TechnicalReport dinamically."""
        start = time.time()
        erros_criticos: list[str] = []
        avisos: list[str] = []
        validation_results: dict[str, dict] = {}
        dimensoes_mm: dict | None = None
        paginas_com_erro: list[int] = []

        file_path = payload.file_path
        
        # 0. Carregamento de Perfil GWG Dinâmico
        from agentes.operarios.shared_tools.gwg.profile_matcher import (
            get_gwg_profile, identify_profile_by_metadata
        )
        profile_key = identify_profile_by_metadata({"produto": payload.produto_detectado or "Papelaria Plana"})
        profile = get_gwg_profile(profile_key)
        
        logger.info(f"[{AGENT_NAME}] Usando perfil dinâmico: {profile['name']}")

        # V-01 & V-02: Geometria Profunda (GWG Standard)
        try:
            from agentes.operarios.shared_tools.gwg.geometry_checker import check_geometry
            geo_results = check_geometry(file_path)
            # Pegamos os resultados da primeira página como referência para o job
            if geo_results:
                for check in geo_results[0]["checks"]:
                    key = f"V01_{check['label'].lower().replace(' ', '_')}"
                    validation_results[key] = check
                    if check["status"] == "ERRO":
                        erros_criticos.append(check.get("codigo", "E_GEO_ERR"))
                    elif check["status"] == "AVISO":
                        avisos.append(check.get("codigo", "W_GEO_WARN"))
        except Exception as exc:
            logger.error(f"Geometria falhou: {exc}")

        # V-03: Safety Margin (Domínio Específico do Operário)
        try:
            from agentes.operarios.operario_papelaria_plana.tools.bleed_checker import (
                check_safety_margin,
            )
            v03 = check_safety_margin(file_path)
            validation_results["V03_margem_seguranca"] = v03
            if v03.get("status") == "ERRO":
                erros_criticos.append(v03.get("codigo", "E003_SAFETY_MARGIN"))
        except Exception as exc:
            logger.error(f"V-03 failed: {exc}")

        # V-04: Resolução Dinâmica (Baseada no Perfil)
        try:
            from agentes.gerente.tools.exiftool_reader import (
                extract_metadata,
                get_resolution_dpi,
            )
            metadata = extract_metadata(file_path)
            x_dpi, y_dpi = get_resolution_dpi(metadata)
            min_dpi = min(x_dpi, y_dpi) if x_dpi > 0 and y_dpi > 0 else 0
            
            min_required = profile["min_image_resolution"]

            if 0 < min_dpi < min_required:
                validation_results["V04_resolucao"] = {
                    "status": "ERRO",
                    "codigo": "E005_LOW_RESOLUTION",
                    "label": "Resolução de Imagem",
                    "found_value": f"{min_dpi} DPI",
                    "expected_value": f">= {min_required} DPI",
                    "meta": {
                        "client": "Resolução insuficiente para o processo de impressão selecionado.",
                        "action": "Utilize imagens com maior resolução ou reduza o tamanho da imagem na arte."
                    }
                }
                erros_criticos.append("E005_LOW_RESOLUTION")
            else:
                validation_results["V04_resolucao"] = {
                    "status": "OK",
                    "label": "Resolução de Imagem",
                    "found_value": f"{min_dpi} DPI" if min_dpi > 0 else "N/A (Vetorial)",
                    "expected_value": f">= {min_required} DPI",
                    "meta": {"client": "Resolução adequada.", "action": "Nenhuma."}
                }
        except Exception as exc:
            logger.warning(f"V-04 failed: {exc}")

        # V-05: Espaço de Cor & TAC (GWG Dinâmico)
        try:
            from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
            v05 = check_color_compliance(file_path, {"produto": profile["name"]})
            validation_results["V05_cor_tac"] = v05
            if v05.get("status") == "REPROVADO":
                erros_criticos.append("E006_COLOR_FAILURE")
        except Exception as exc:
            logger.error(f"V-05 failed: {exc}")

        # V-07: Fontes (GWG Embedding)
        try:
            from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg
            v07 = check_fonts_gwg(file_path)
            validation_results["V07_fontes"] = v07
            if v07.get("status") == "ERRO":
                erros_criticos.append(v07.get("codigo", "E004_FONT_NOT_EMBEDDED"))
        except Exception as exc:
            logger.error(f"V-07 failed: {exc}")

        # V-00c: Overprint & OPM (GWG 5.0)
        try:
            from agentes.operarios.shared_tools.gwg.opm_checker import check_opm
            v00c = check_opm(file_path)
            validation_results["V00c_overprint"] = v00c
            codigo_opm = v00c.get("codigo")
            if codigo_opm:
                if codigo_opm.startswith("E_"):
                    erros_criticos.append(codigo_opm)
                else:
                    avisos.append(codigo_opm)
        except Exception as exc:
            logger.error(f"V-00c failed: {exc}")

        # V-00d: ICC Profile & OutputIntent (GWG Rigoroso)
        try:
            from agentes.operarios.shared_tools.gwg.icc_checker import check_icc
            v00d = check_icc(file_path)
            validation_results["V00d_icc"] = v00d
            codigo_icc = v00d.get("codigo")
            if codigo_icc:
                if codigo_icc.startswith("E_"):
                    erros_criticos.append(codigo_icc)
                else:
                    avisos.append(codigo_icc)
        except Exception as exc:
            logger.error(f"V-00d failed: {exc}")

        # Calculate status final
        from agentes.validador.agent import calcular_status_final
        status_final = calcular_status_final(erros_criticos, avisos)

        elapsed_ms = int((time.time() - start) * 1000)

        return TechnicalReport(
            job_id=payload.job_id,
            agent=AGENT_NAME,
            produto_detectado=f"{payload.produto_detectado or 'Papelaria Plana'} ({profile['name']})",
            status=status_final,
            erros_criticos=erros_criticos,
            avisos=avisos,
            validation_results=validation_results,
            processing_time_ms=elapsed_ms,
            timestamp=datetime.now(timezone.utc),
            dimensoes_mm=dimensoes_mm,
            paginas_com_erro=paginas_com_erro,
        )
