"""
Agente Validador — 100% deterministic report engine.

Receives TechnicalReport JSON from Operários, applies Rule 2 (Anti-RAG):
- NEVER consults embeddings, vector stores, or external knowledge bases
- NEVER uses LLM to generate report text
- Uses ONLY the hardcoded messages_table.py
- Status is mathematical: errors → REPROVADO, no exceptions
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.api.schemas import FinalReport, TechnicalReport
from agentes.validador.messages_table import (
    SUMMARY_TEMPLATES,
    get_message,
)

logger = logging.getLogger(__name__)


def calcular_status_final(erros: list[str], avisos: list[str]) -> str:
    """Determine the final status — completely deterministic.

    Zero AI. Zero RAG. Purely mathematical.

    Args:
        erros: List of error codes (E-prefixed = critical).
        avisos: List of warning codes (W-prefixed).

    Returns:
        'REPROVADO', 'APROVADO_COM_RESSALVAS', or 'APROVADO'.
    """
    erros_reais = [e for e in erros if e.startswith("E")]
    if erros_reais:
        return "REPROVADO"
    if avisos:
        return "APROVADO_COM_RESSALVAS"
    return "APROVADO"


class AgenteValidador:
    """Deterministic report generator — transforms technical JSON into client report."""

    def processar(
        self,
        report: TechnicalReport,
        locale: str = "pt-BR",
    ) -> FinalReport:
        """Process a TechnicalReport and produce a FinalReport.

        Args:
            report: Technical report from an Operário.
            locale: Client locale for message translation.

        Returns:
            FinalReport with localized messages.
        """
        # Step 1: Determine final status (deterministic)
        status = calcular_status_final(report.erros_criticos, report.avisos)

        # Build codigo → check lookup from validation_results so we can
        # repassar found_value/expected_value originais de cada checker.
        check_index: dict[str, dict] = {}
        for entry in (report.validation_results or {}).values():
            if not isinstance(entry, dict):
                continue
            # Entradas simples
            c = entry.get("codigo")
            if c and c not in check_index:
                check_index[c] = entry
            # Entradas com sub-diagnósticos (ex.: icc_checker.diagnostics,
            # compression_checker.issues)
            for sub in entry.get("diagnostics", []) or []:
                sc = sub.get("codigo")
                if sc and sc not in check_index:
                    check_index[sc] = sub
            for iss in entry.get("issues", []) or []:
                ic = iss.get("codigo")
                if ic and ic not in check_index:
                    check_index[ic] = iss
            # Normalized per-page entries (geometry)
            for pc in entry.get("per_page_checks", []) or []:
                pcc = pc.get("codigo")
                if pcc and pcc not in check_index:
                    check_index[pcc] = pc

        def _enrich(code: str, severidade: str) -> dict:
            msg = get_message(code, locale)
            src = check_index.get(code, {})
            titulo = msg.get("titulo") or src.get("label") or code
            descricao = msg.get("descricao") or src.get("descricao") or ""
            acao = msg.get("acao") or (src.get("meta", {}) or {}).get("action", "")
            item = {
                "severidade": severidade,
                "codigo": code,
                "titulo": titulo,
                "descricao": descricao,
                "acao_corretiva": acao,
                "found_value": src.get("found_value"),
                "expected_value": src.get("expected_value"),
            }
            return item

        # Step 2: Critical errors
        erros_formatted: list[dict] = [
            _enrich(code, "CRÍTICO") for code in report.erros_criticos
        ]

        # Step 3: Warnings
        avisos_formatted: list[dict] = [
            _enrich(code, "AVISO") for code in report.avisos
        ]

        # Step 4: Build summary text
        # --- INTELLIGENT AI SUMMARY ---
        import asyncio
        from app.api.llm_client import gerar_relatorio_humanizado_llm
        
        resumo_llm = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                 import concurrent.futures
                 with concurrent.futures.ThreadPoolExecutor() as pool:
                      resumo_llm = pool.submit(asyncio.run, gerar_relatorio_humanizado_llm(
                          status, report.produto_detectado, erros_formatted, avisos_formatted
                      )).result()
            else:
                 resumo_llm = loop.run_until_complete(gerar_relatorio_humanizado_llm(
                     status, report.produto_detectado, erros_formatted, avisos_formatted
                 ))
        except RuntimeError:
            resumo_llm = asyncio.run(gerar_relatorio_humanizado_llm(status, report.produto_detectado, erros_formatted, avisos_formatted))
        except Exception as exc:
            logger.warning(f"[Validador] LLM call failed or skipped: {exc}")

        if resumo_llm:
            resumo = resumo_llm
        else:
            templates = SUMMARY_TEMPLATES.get(locale, SUMMARY_TEMPLATES["pt-BR"])
            resumo_base = templates.get(status, "")

            if locale == "pt-BR":
                resumo = (
                    f"RESULTADO: {status}\n"
                    f"Produto detectado: {report.produto_detectado}\n"
                    f"Total de erros críticos: {len(report.erros_criticos)}\n"
                    f"Total de avisos: {len(report.avisos)}\n\n"
                    f"{resumo_base}"
                )
            elif locale == "en-US":
                resumo = (
                    f"RESULT: {status}\n"
                    f"Product detected: {report.produto_detectado}\n"
                    f"Critical errors: {len(report.erros_criticos)} | "
                    f"Warnings: {len(report.avisos)}\n\n"
                    f"{resumo_base}"
                )
            elif locale == "es-ES":
                resumo = (
                    f"RESULTADO: {status}\n"
                    f"Producto detectado: {report.produto_detectado}\n"
                    f"Errores críticos: {len(report.erros_criticos)} | "
                    f"Advertencias: {len(report.avisos)}\n\n"
                    f"{resumo_base}"
                )
            else:
                resumo = resumo_base

        # Step 5: Build technical details
        is_gwg_compliant = (status == "APROVADO")
        
        detalhes_tecnicos = {
            "agent_processador": report.agent,
            "tempo_processamento_ms": report.processing_time_ms,
            "gwg_2022_compliance": {
                "status": "COMPLIANT" if is_gwg_compliant else "NON_COMPLIANT",
                "specification": "GWG 2022.1 Prepress",
                "details": "O arquivo atende a todos os requisitos técnicos da Ghent Workgroup." if is_gwg_compliant else "O arquivo apresenta violações técnicas em relação às normas GWG 2022."
            }
        }
        if report.dimensoes_mm:
            detalhes_tecnicos["dimensoes_detectadas"] = (
                f"{report.dimensoes_mm.get('width', 0)} × "
                f"{report.dimensoes_mm.get('height', 0)}mm"
            )
        if report.paginas_com_erro:
            detalhes_tecnicos["paginas_com_erro"] = report.paginas_com_erro

        # Include raw validation results
        detalhes_tecnicos["validacoes"] = report.validation_results

        logger.info(
            f"[Validador] Job {report.job_id}: status={status}, "
            f"gwg_compliant={is_gwg_compliant}, "
            f"errors={len(report.erros_criticos)}"
        )

        return FinalReport(
            job_id=report.job_id,
            status=status,
            produto=report.produto_detectado,
            avaliado_em=datetime.now(timezone.utc),
            resumo=resumo,
            erros=erros_formatted,
            avisos=avisos_formatted,
            detalhes_tecnicos=detalhes_tecnicos,
        )
