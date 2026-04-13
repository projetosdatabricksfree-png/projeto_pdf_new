"""
Celery tasks for the validation pipeline.

Tasks: task_route, task_process_*, task_validate, task_log
Each task bridges the Celery worker with the corresponding agent.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _pages_from_detail(detail: dict) -> Optional[list[int]]:
    """Extract affected page numbers from operário/validador detail dicts."""
    raw = detail.get("paginas") or detail.get("pages") or detail.get("pages_affected")
    if not raw or not isinstance(raw, list):
        return None
    out: list[int] = []
    for p in raw:
        try:
            out.append(int(p))
        except (TypeError, ValueError):
            continue
    return out or None


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _update_status(job_id: str, status: str) -> None:
    """Update job status in the database."""
    from app.database.session import async_session_factory
    from app.database.crud import update_job_status, create_event

    async with async_session_factory() as db:
        await update_job_status(db, job_id, status)
        await create_event(
            db,
            job_id=job_id,
            agent_name="worker",
            event_type="STATUS_CHANGE",
            event_level="INFO",
            payload=json.dumps({"to": status}),
        )
        await db.commit()


@celery_app.task(name="workers.tasks.task_route", bind=True, max_retries=3)
def task_route(self, job_payload_json: str, job_metadata_json: str = "{}") -> str:
    """Route a job to the correct operário via the Gerente agent.

    Args:
        job_payload_json: Serialized JobPayload
        job_metadata_json: Extra metadata (gramatura, encadernação, etc.)

    Returns:
        Serialized RoutingPayload
    """
    logger.critical(f"TASK_RECEIVED: task_route starting for job {job_payload_json}")
    from app.api.schemas import JobPayload
    from agentes.gerente.agent import AgenteGerente

    payload = JobPayload.model_validate_json(job_payload_json)
    job_metadata = json.loads(job_metadata_json)

    logger.info(f"[task_route] Routing job {payload.job_id}")

    # Update status to ROUTING
    _run_async(_update_status(payload.job_id, "ROUTING"))

    # Execute routing
    gerente = AgenteGerente()
    routing_result = gerente.processar(payload, job_metadata)

    # Dispatch to the correct operário task
    route_to = routing_result.route_to
    routing_json = routing_result.model_dump_json()

    task_map = {
        "operario_papelaria_plana": task_process_papelaria,
        "operario_editoriais": task_process_editoriais,
        "operario_dobraduras": task_process_dobraduras,
        "operario_cortes_especiais": task_process_cortes,
        "operario_projetos_cad": task_process_cad,
        "especialista": task_process_especialista,
    }

    target_task = task_map.get(route_to)
    if target_task:
        # Update status to the specific stage
        target_status = "PROBING" if route_to == "especialista" else "PROCESSING"
        _run_async(_update_status(payload.job_id, target_status))
        target_task.delay(routing_json)
    else:
        logger.error(f"[task_route] Unknown route: {route_to}")
        _run_async(_update_status(payload.job_id, "FAILED"))

    return routing_json


def _run_operario(routing_json: str, agent_class_path: str) -> str:
    """Generic operário runner."""
    from app.api.schemas import RoutingPayload
    import importlib

    payload = RoutingPayload.model_validate_json(routing_json)
    logger.info(f"[operario] Processing job {payload.job_id} via {payload.route_to}")

    # Dynamically import the agent
    module_path, class_name = agent_class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)

    agent = agent_class()
    report = agent.processar(payload)

    # Dispatch to validador
    report_json = report.model_dump_json()
    task_validate.delay(report_json)

    return report_json


@celery_app.task(name="workers.tasks.task_process_papelaria", bind=True)
def task_process_papelaria(self, routing_json: str) -> str:
    """Process a papelaria plana job."""
    return _run_operario(
        routing_json,
        "agentes.operarios.operario_papelaria_plana.agent.OperarioPapelariaPlana",
    )


@celery_app.task(name="workers.tasks.task_process_editoriais", bind=True)
def task_process_editoriais(self, routing_json: str) -> str:
    """Process an editorial job."""
    return _run_operario(
        routing_json,
        "agentes.operarios.operario_editoriais.agent.OperarioEditoriais",
    )


@celery_app.task(name="workers.tasks.task_process_dobraduras", bind=True)
def task_process_dobraduras(self, routing_json: str) -> str:
    """Process a dobraduras job."""
    return _run_operario(
        routing_json,
        "agentes.operarios.operario_dobraduras.agent.OperarioDobraduras",
    )


@celery_app.task(name="workers.tasks.task_process_cortes", bind=True)
def task_process_cortes(self, routing_json: str) -> str:
    """Process a cortes especiais job."""
    return _run_operario(
        routing_json,
        "agentes.operarios.operario_cortes_especiais.agent.OperarioCortesEspeciais",
    )


@celery_app.task(name="workers.tasks.task_process_cad", bind=True)
def task_process_cad(self, routing_json: str) -> str:
    """Process a projetos CAD job."""
    return _run_operario(
        routing_json,
        "agentes.operarios.operario_projetos_cad.agent.OperarioProjetosCAD",
    )


@celery_app.task(name="workers.tasks.task_process_especialista", bind=True)
def task_process_especialista(self, routing_json: str) -> str:
    """Perform deep probing via the Specialist agent.

    Publishes the refined routing decision to queue:routing_decisions instead of
    dispatching directly to operário tasks.  This decouples the Especialista from
    the Operários and prevents Celery thread-pool deadlocks (Rule 3).
    """
    from app.api.schemas import RoutingPayload
    from agentes.especialista.agent import AgenteEspecialista

    payload = RoutingPayload.model_validate_json(routing_json)
    logger.info(f"[especialista] Deep probing job {payload.job_id}")

    especialista = AgenteEspecialista()
    decision = especialista.processar(
        file_path=payload.file_path,
        metadata=payload.metadata_snapshot,
    )

    # Mapping reasons to human product names
    product_map = {
        "SPOT_COLOR_FACA_DETECTED": "Cortes Especiais",
        "VARIABLE_PAGE_WIDTHS_CREEP_DETECTED": "Dobraduras",
        "EMBEDDED_FONTS_MULTIPAGE": "Editorial",
        "PURE_VECTOR_LARGE_FORMAT": "Projeto CAD",
    }
    detected_p = product_map.get(decision["reason"], "Papelaria Plana")

    route_map = {
        "SPOT_COLOR_FACA_DETECTED": "operario_cortes_especiais",
        "VARIABLE_PAGE_WIDTHS_CREEP_DETECTED": "operario_dobraduras",
        "EMBEDDED_FONTS_MULTIPAGE": "operario_editoriais",
        "PURE_VECTOR_LARGE_FORMAT": "operario_projetos_cad",
    }
    route_to = decision.get("route_to") or route_map.get(
        decision["reason"], "operario_papelaria_plana"
    )

    routing_result = RoutingPayload(
        job_id=payload.job_id,
        file_path=payload.file_path,
        file_size_bytes=payload.file_size_bytes,
        route_to=route_to,
        confidence=decision["confidence"],
        reason=decision["reason"],
        metadata_snapshot=payload.metadata_snapshot,
        client_locale=payload.client_locale,
        job_metadata=payload.job_metadata,
        produto_detectado=detected_p
    )
    refined_routing_json = routing_result.model_dump_json()

    # Publish to queue:routing_decisions — consumed by task_receive_routing_decision
    task_receive_routing_decision.apply_async(
        args=[refined_routing_json],
        queue="queue:routing_decisions",
    )

    return refined_routing_json


@celery_app.task(name="workers.tasks.task_receive_routing_decision", bind=True)
def task_receive_routing_decision(self, routing_json: str) -> str:
    """Consume routing decisions from queue:routing_decisions and dispatch to operário.

    This is the explicit, dedicated consumer for queue:routing_decisions (Rule 3 —
    Deadlock Prevention).  Decoupling Especialista output from Operário input via a
    separate queue prevents thread exhaustion when a single worker pool handles both
    ends of the pipeline.

    Args:
        routing_json: Serialized RoutingPayload produced by task_process_especialista.

    Returns:
        The same routing_json, for chain continuations.
    """
    from app.api.schemas import RoutingPayload

    payload = RoutingPayload.model_validate_json(routing_json)
    logger.info(
        f"[routing_decision] job={payload.job_id} → {payload.route_to} "
        f"(confidence={payload.confidence:.2f})"
    )

    task_map = {
        "operario_papelaria_plana": task_process_papelaria,
        "operario_editoriais": task_process_editoriais,
        "operario_dobraduras": task_process_dobraduras,
        "operario_cortes_especiais": task_process_cortes,
        "operario_projetos_cad": task_process_cad,
    }

    target_task = task_map.get(payload.route_to)
    if target_task:
        _run_async(_update_status(payload.job_id, "PROCESSING"))
        target_task.delay(routing_json)
    else:
        logger.error(f"[routing_decision] Unknown route_to: '{payload.route_to}'")
        _run_async(_update_status(payload.job_id, "FAILED"))

    return routing_json


@celery_app.task(name="workers.tasks.task_validate", bind=True)
def task_validate(self, report_json: str) -> str:
    """Run the Validador agent on a technical report.

    Produces the final verdict (APROVADO/REPROVADO/APROVADO_COM_RESSALVAS).
    """
    logger.critical(f"TASK_RECEIVED: task_validate starting")
    from app.api.schemas import TechnicalReport
    from agentes.validador.agent import AgenteValidador

    report = TechnicalReport.model_validate_json(report_json)
    logger.info(f"[task_validate] Validating job {report.job_id}")

    # Update status
    _run_async(_update_status(report.job_id, "VALIDATING"))

    validador = AgenteValidador()
    final_report = validador.processar(report)

    # Persist final results
    _run_async(_persist_final_report(
        report.job_id,
        final_report,
        detected_product=report.produto_detectado,
        processing_agent=report.agent
    ))

    # Log completion
    task_log.delay(json.dumps({
        "job_id": report.job_id,
        "agent_name": "validador",
        "event_type": "VALIDATION",
        "event_level": "INFO",
        "payload": final_report.model_dump(),
    }, default=str))

    return final_report.model_dump_json()


async def _persist_final_report(
    job_id: str,
    final_report,
    detected_product: Optional[str] = None,
    processing_agent: Optional[str] = None
) -> None:
    """Persist the final report and update job status."""
    from app.database.session import async_session_factory
    from app.database.crud import complete_job, upsert_validation_result

    async with async_session_factory() as db:
        # Save each validation detail
        detalhes = final_report.detalhes_tecnicos or {}
        
        # If technical details are nested (standard for this pipeline)
        if "validacoes" in detalhes and isinstance(detalhes["validacoes"], dict):
            checks_to_save = detalhes["validacoes"]
        else:
            checks_to_save = detalhes

        for check_code, detail in checks_to_save.items():
            # Handle both dicts (legacy) and Pydantic models (current)
            if hasattr(detail, "model_dump"):
                detail_dict = detail.model_dump()
            elif isinstance(detail, dict):
                detail_dict = detail
            else:
                continue

            await upsert_validation_result(
                db,
                job_id=job_id,
                agent_name="validador",
                check_code=check_code,
                check_name=detail_dict.get("label") or detail_dict.get("check_name") or check_code,
                status=detail_dict.get("status", "OK"),
                error_code=detail_dict.get("codigo") or detail_dict.get("error_code"),
                value_found=str(detail_dict.get("found_value") or detail_dict.get("value_found") or detail_dict.get("valor", "")),
                value_expected=str(detail_dict.get("expected_value") or detail_dict.get("value_expected") or ""),
                pages_affected=_pages_from_detail(detail_dict),
            )

        # Complete the job
        await complete_job(
            db,
            job_id=job_id,
            final_status=final_report.status,
            error_count=len(final_report.erros),
            warning_count=len(final_report.avisos),
            detected_product=detected_product,
            processing_agent=processing_agent,
        )
        await db.commit()


@celery_app.task(name="workers.tasks.task_log", bind=True)
def task_log(self, event_json: str) -> None:
    """Persist an audit event to the database."""
    from agentes.logger.agent import AgenteLogger

    event_data = json.loads(event_json)
    logger_agent = AgenteLogger()
    _run_async(logger_agent.registrar_evento(event_data))
