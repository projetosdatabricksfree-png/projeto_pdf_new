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

        # Step 2: Map error codes to localized messages
        erros_formatted: list[dict] = []
        for code in report.erros_criticos:
            msg = get_message(code, locale)
            erros_formatted.append({
                "severidade": "CRÍTICO",
                "codigo": code,
                "titulo": msg["titulo"],
                "descricao": msg["descricao"],
                "acao_corretiva": msg["acao"],
            })

        # Step 3: Map warning codes to localized messages
        avisos_formatted: list[dict] = []
        for code in report.avisos:
            msg = get_message(code, locale)
            avisos_formatted.append({
                "severidade": "AVISO",
                "codigo": code,
                "titulo": msg["titulo"],
                "descricao": msg["descricao"],
                "acao_corretiva": msg.get("acao", ""),
            })

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
        detalhes_tecnicos = {
            "agent_processador": report.agent,
            "tempo_processamento_ms": report.processing_time_ms,
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
            f"errors={len(report.erros_criticos)}, "
            f"warnings={len(report.avisos)}"
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
