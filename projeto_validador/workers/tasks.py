"""
Celery tasks for the validation pipeline.

Tasks: task_route, task_process_*, task_validate, task_log
Each task bridges the Celery worker with the corresponding agent.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

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
    from app.database.crud import create_event, update_job_status
    from app.database.session import async_session_factory

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
    from agentes.gerente.agent import AgenteGerente
    from app.api.schemas import JobPayload

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
    import importlib

    from app.api.schemas import RoutingPayload

    payload = RoutingPayload.model_validate_json(routing_json)
    logger.info(f"[operario] Processing job {payload.job_id} via {payload.route_to}")

    # Dynamically import the agent
    module_path, class_name = agent_class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)

    agent = agent_class()
    report = agent.processar(payload)

    # Forward the Bronze file path so the Gold layer can locate it downstream.
    if report.file_path is None:
        report.file_path = payload.file_path

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
    from agentes.especialista.agent import AgenteEspecialista
    from app.api.schemas import RoutingPayload

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
    logger.critical("TASK_RECEIVED: task_validate starting")
    from agentes.validador.agent import AgenteValidador
    from app.api.schemas import TechnicalReport

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

    # Gold layer kickoff — only when there are critical errors AND the registry
    # can handle at least one of them. Warnings-only jobs skip remediation.
    if final_report.status != "APROVADO" and report.file_path:
        from agentes.remediadores.registry import supported_codes
        fixable = {vr.codigo for vr in report.validation_results.values()
                   if vr.codigo in supported_codes() and vr.status in {"REPROVADO", "AVISO"}}
        if fixable:
            logger.info(f"[task_validate] dispatching Gold remediation for {report.job_id}: {fixable}")
            task_remediate.delay(report.model_dump_json())

    return final_report.model_dump_json()


async def _persist_final_report(
    job_id: str,
    final_report,
    detected_product: Optional[str] = None,
    processing_agent: Optional[str] = None
) -> None:
    """Persist the final report and update job status."""
    from app.database.crud import complete_job, upsert_validation_result
    from app.database.session import async_session_factory

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
                value_found=str(
                    detail_dict.get("found_value")
                    or detail_dict.get("value_found")
                    or detail_dict.get("valor", "")
                ),
                value_expected=str(
                    detail_dict.get("expected_value") or detail_dict.get("value_expected") or ""
                ),
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


# ─── Gold Layer ──────────────────────────────────────────────────────────────

# B-04: Canonical remediation order — geometry first, then transparency,
# then color space, then font embedding, then resolution.
# Running transparency flattening (E_TGROUP_CS_INVALID) before color conversion
# ensures GS's PDF 1.3 flatten step doesn't recreate RGB objects that the
# colour remediator would have already handled.
_REMEDIATION_ORDER: list[str] = [
    "G002",                    # Bleed (geometry)
    "E004",                    # Safety margin (geometry)
    "E_TGROUP_CS_INVALID",     # Transparency flatten (must precede colour conversion)
    "E_OUTPUTINTENT_MISSING",  # OutputIntent injection (after flatten, before full colour)
    "E006_FORBIDDEN_COLORSPACE",  # Forbidden colourspace conversion
    "E_TAC_EXCEEDED",          # TAC re-separation (same GS path as forbidden CS)
    "E008_NON_EMBEDDED_FONTS", # Font embedding
    "W_COURIER_SUBSTITUTION",  # Courier substitution (font family)
    "W003_BORDERLINE_RESOLUTION",  # Resolution upsampling
]


def _remediation_order(codes: list[str]) -> list[str]:
    """Return *codes* sorted by the canonical remediation order.

    Codes not present in the canonical list are appended at the end in their
    original relative order (stable sort).

    Args:
        codes: List of error/warning codes to sort.

    Returns:
        Sorted list with canonical order applied.
    """
    canonical_index = {code: idx for idx, code in enumerate(_REMEDIATION_ORDER)}
    # Use len(_REMEDIATION_ORDER) as sentinel for unknown codes so they sort last.
    return sorted(codes, key=lambda c: canonical_index.get(c, len(_REMEDIATION_ORDER)))


@celery_app.task(name="workers.tasks.task_remediate", bind=True)
def task_remediate(self, technical_report_json: str) -> str:
    """Run deterministic Gold-layer remediation on a rejected job.

    Reads the TechnicalReport from task_validate, dispatches each fixable
    ValidationResult to the matching Remediator in sequence (order matters —
    color conversion before font embedding before resolution tweaks), then
    hands the Gold candidate to task_validate_gold.

    Returns the serialized RemediationReport.
    """
    from pathlib import Path

    from agentes.remediadores.registry import get_remediator
    from app.api.schemas import (
        RemediationAction,
        RemediationReport,
        TechnicalReport,
    )

    logger.critical("TASK_RECEIVED: task_remediate starting")
    report = TechnicalReport.model_validate_json(technical_report_json)

    if not report.file_path:
        logger.error(f"[task_remediate] missing file_path for job {report.job_id}")
        return RemediationReport(
            job_id=report.job_id,
            input_path="",
            output_path="",
            overall_success=False,
        ).model_dump_json()

    _run_async(_update_status(report.job_id, "REMEDIATING"))

    bronze = Path(report.file_path)
    gold = bronze.with_name(f"{bronze.stem}_gold.pdf")
    # Work on a scratch copy so failed remediators don't corrupt Bronze.
    import shutil
    scratch = bronze.with_name(f"{bronze.stem}_scratch.pdf")
    shutil.copy2(bronze, scratch)

    actions: list[RemediationAction] = []
    # B-04: Sort by canonical remediation order (geometry → transparency → colour →
    # font → resolution). _remediation_order guarantees upstream fixes never invalidate
    # downstream ones (e.g. flatten rebuilds objects that resolution_remediator needs).
    ordered_codes = _remediation_order(
        [vr.codigo for vr in report.validation_results.values() if vr.codigo]
    )
    code_to_items = {
        vr.codigo: (k, vr)
        for k, vr in report.validation_results.items()
        if vr.codigo
    }
    items = [code_to_items[c] for c in ordered_codes if c in code_to_items]

    for _check_name, vr in items:
        if not vr.codigo or vr.status not in {"REPROVADO", "AVISO"}:
            continue
        remediator = get_remediator(vr.codigo)
        if remediator is None:
            continue

        next_scratch = bronze.with_name(f"{bronze.stem}_scratch_{vr.codigo}.pdf")
        try:
            action = remediator.remediate(scratch, next_scratch, vr)
        except Exception as exc:
            logger.exception("Remediator %s crashed: %s", remediator.name, exc)
            action = RemediationAction(
                codigo=vr.codigo,
                remediator=remediator.name,
                success=False,
                quality_loss_warnings=[f"Remediator crashed: {exc}"],
                technical_log=str(exc),
            )
        actions.append(action)

        if action.success and next_scratch.exists():
            # Chain: each successful step becomes input for the next.
            shutil.move(str(next_scratch), str(scratch))
        else:
            # Keep previous scratch; do not advance pipeline on failure.
            if next_scratch.exists():
                next_scratch.unlink(missing_ok=True)

    # Post-Sprint A contract: always produce a Gold candidate from whatever
    # scratch state we have. success=False on an action means a technical failure
    # (binary missing, timeout) — not a policy decision.  Quality degradations
    # are recorded in quality_loss_warnings and do not block delivery.
    overall_success = bool(actions) and all(a.success for a in actions)
    has_quality_warnings = any(a.quality_loss_warnings for a in actions)

    gold_produced = False
    if scratch.exists():
        shutil.move(str(scratch), str(gold))
        gold_produced = True
    else:
        scratch.unlink(missing_ok=True)

    remediation_report = RemediationReport(
        job_id=report.job_id,
        input_path=str(bronze),
        output_path=str(gold) if gold_produced else "",
        actions=actions,
        overall_success=overall_success,
    )

    task_log.delay(json.dumps({
        "job_id": report.job_id,
        "agent_name": "remediador",
        "event_type": "REMEDIATION",
        "event_level": "INFO" if overall_success else "WARNING",
        "payload": remediation_report.model_dump(),
    }, default=str))

    if gold_produced:
        task_validate_gold.delay(remediation_report.model_dump_json())
    else:
        # Technical failure: could not produce any output file
        _run_async(_update_status(report.job_id, "GOLD_REJECTED"))

    return remediation_report.model_dump_json()


# ─── Sprint C: VeraPDF rule → remediator code mapping ────────────────────────

# VeraPDF rule IDs follow ISO 15930-7 clause numbering.
# Format: "{clause}.{testNumber}" — e.g. "6.2.2.1".
# Only rules where a known remediator can fix the issue are listed here.
_VERAPDF_RULE_MAP: dict[str, str] = {
    # 6.2.x — OutputIntent requirements
    "6.2.2.1": "E_OUTPUTINTENT_MISSING",  # /OutputIntents absent
    "6.2.2.2": "E_OUTPUTINTENT_MISSING",  # wrong /S subtype
    "6.2.3.1": "E_OUTPUTINTENT_MISSING",  # missing DestOutputProfile
    "6.2.4.1": "E_OUTPUTINTENT_MISSING",  # corrupt DestOutputProfile
    # 6.3.x — Colour space requirements
    "6.3.2.1": "E006_FORBIDDEN_COLORSPACE",  # RGB device colour
    "6.3.3.1": "E006_FORBIDDEN_COLORSPACE",  # CalRGB colour
    "6.3.5.1": "E_TAC_EXCEEDED",            # total area coverage
    # 6.4.x — Transparency groups
    "6.4.1.1": "E_TGROUP_CS_INVALID",  # TGroup CS != DeviceCMYK
    "6.4.2.1": "E_TGROUP_CS_INVALID",  # TGroup /CS absent
}


def _map_verapdf_rule_to_code(rule_id: str) -> str | None:
    """Map a VeraPDF rule clause ID to a known remediator error code.

    C-04 AC1: initial dictionary covering rules 6.2.x, 6.3.x, 6.4.x.
    Returns None when no remediator handles the rule.
    """
    return _VERAPDF_RULE_MAP.get(rule_id)


def _derive_codes_from_violations(violations) -> list[str]:
    """Collect distinct remediable codes from a VeraPDF violation list."""
    codes: list[str] = []
    seen: set[str] = set()
    for v in violations:
        code = _map_verapdf_rule_to_code(v.rule_id)
        if code and code not in seen:
            codes.append(code)
            seen.add(code)
    return codes


@celery_app.task(name="workers.tasks.task_validate_gold", bind=True)
def task_validate_gold(self, remediation_report_json: str, _retry_pass: int = 0) -> str:
    """Run validador_final + VeraPDF against the Gold candidate.

    Sprint C additions:
    - Dispatches task_verapdf_audit to queue:verapdf after primary validation.
    - C-04: up to 1 re-remediation pass when VeraPDF finds mappable violations.

    Emits a GoldValidationReport and updates job status to either
    GOLD_DELIVERED or GOLD_DELIVERED_WITH_WARNINGS.
    The Bronze file is never touched.
    """
    from pathlib import Path

    from agentes.validador_final.agent import validate_gold
    from app.api.schemas import RemediationReport

    logger.critical("TASK_RECEIVED: task_validate_gold starting (pass=%d)", _retry_pass)
    remediation = RemediationReport.model_validate_json(remediation_report_json)
    _run_async(_update_status(remediation.job_id, "GOLD_VALIDATING"))

    gold_path = Path(remediation.output_path)

    # ── VeraPDF audit (async, dedicated queue) ───────────────────────────────
    # AC5 (C-02): dispatch to validador-verapdf container after producing Gold.
    # We also attempt inline VeraPDF for the validate_gold fallback chain.
    verapdf_report = None
    try:
        from app.api.schemas import VeraPDFReport
        from workers.tasks_verapdf import _parse_verapdf_json, run_verapdf, task_verapdf_audit

        # Try inline VeraPDF (works if binary is on PATH in this container).
        ok, stdout, stderr = run_verapdf(gold_path)
        if ok:
            parsed = _parse_verapdf_json(stdout, remediation.job_id)
            verapdf_report = VeraPDFReport(
                job_id=remediation.job_id,
                passed=parsed["passed"],
                profile=parsed.get("profile", "PDF/X-4"),
                rule_violations=parsed.get("rule_violations", []),
                raw_json=stdout,
                gold_path=str(gold_path),
            )
        else:
            # Binary absent in this container — dispatch to dedicated queue.
            task_verapdf_audit.apply_async(
                args=[remediation.job_id, str(gold_path)],
                queue="queue:verapdf",
            )
    except Exception as exc:
        logger.debug("[task_validate_gold] VeraPDF probe skipped: %s", exc)

    # ── C-04: Re-remediation loop (max 1 retry) ──────────────────────────────
    if (
        verapdf_report is not None
        and not verapdf_report.passed
        and _retry_pass == 0
        and verapdf_report.rule_violations
    ):
        remediable = _derive_codes_from_violations(verapdf_report.rule_violations)
        if remediable:
            logger.info(
                "[task_validate_gold] VeraPDF residuals — re-remediation pass 1: %s",
                remediable,
            )
            # Rebuild a minimal TechnicalReport to drive task_remediate.
            from app.api.schemas import ValidationResult as VR

            fake_vr: dict[str, VR] = {
                c: VR(status="REPROVADO", codigo=c, found_value="verapdf_residual")
                for c in remediable
            }
            # Inline execution to avoid infinite celery dispatch (AC3).
            import shutil as _shutil
            gold_repass = gold_path.with_name(f"{gold_path.stem}_repass.pdf")
            _shutil.copy2(gold_path, gold_repass)

            from agentes.remediadores.registry import get_remediator
            from app.api.schemas import RemediationAction, RemediationReport as RR

            scratch = gold_repass
            repass_actions: list[RemediationAction] = []
            for code in _remediation_order(remediable):
                vr_item = fake_vr.get(code)
                if vr_item is None:
                    continue
                remediator = get_remediator(code)
                if remediator is None:
                    continue
                next_s = gold_path.with_name(f"{gold_path.stem}_rp_{code}.pdf")
                try:
                    action = remediator.remediate(scratch, next_s, vr_item)
                except Exception as exc:
                    logger.exception("[repass] remediator %s crashed: %s", code, exc)
                    action = RemediationAction(
                        codigo=code,
                        remediator=getattr(remediator, "name", code),
                        success=False,
                        quality_loss_warnings=[f"crash: {exc}"],
                    )
                repass_actions.append(action)
                if action.success and next_s.exists():
                    _shutil.move(str(next_s), str(scratch))
                elif next_s.exists():
                    next_s.unlink(missing_ok=True)

            if scratch.exists() and str(scratch) != str(gold_repass):
                _shutil.move(str(scratch), str(gold_path))
            elif gold_repass.exists():
                _shutil.move(str(gold_repass), str(gold_path))

            # Second-pass validation — _retry_pass=1 prevents infinite recursion.
            repass_report = RR(
                job_id=remediation.job_id,
                input_path=remediation.input_path,
                output_path=str(gold_path),
                actions=repass_actions,
                overall_success=all(a.success for a in repass_actions),
            )
            return task_validate_gold(repass_report.model_dump_json(), _retry_pass=1)

    # ── Primary validate_gold ─────────────────────────────────────────────────
    verdict = validate_gold(remediation.job_id, gold_path, verapdf_report=verapdf_report)

    task_log.delay(json.dumps({
        "job_id": remediation.job_id,
        "agent_name": "validador_final",
        "event_type": "GOLD_VALIDATION",
        "event_level": "INFO" if verdict.is_gold else "ERROR",
        "payload": verdict.model_dump(),
    }, default=str))

    # Post-Sprint A: is_gold is informational only. The file is always delivered.
    # GOLD_DELIVERED     → is_gold=True (fully compliant)
    # GOLD_DELIVERED_WITH_WARNINGS → is_gold=False but _gold.pdf exists
    final_status = "GOLD_DELIVERED" if verdict.is_gold else "GOLD_DELIVERED_WITH_WARNINGS"
    _run_async(_update_status(remediation.job_id, final_status))
    return verdict.model_dump_json()
