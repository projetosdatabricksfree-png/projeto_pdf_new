"""
Job endpoints: upload, status polling, and final report retrieval.

Implements streaming upload (8MB chunks) to comply with Rule 1 (Anti-OOM).
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    FinalReport,
    JobCreatedResponse,
    JobPayload,
    JobStatusResponse,
)
from app.database.crud import (
    complete_job,
    create_event,
    create_job,
    get_job,
    get_job_validation_results,
)
from app.database.session import get_db

router = APIRouter(prefix="/api/v1", tags=["jobs"])

# 8 MB chunk size for streaming upload — Rule 1: Anti-OOM
CHUNK_SIZE: int = 8 * 1024 * 1024

VOLUME_PATH: str = os.getenv("VOLUME_PATH", "./volumes/uploads")

ALLOWED_CONTENT_TYPES: set[str] = {
    "application/pdf",
    "image/tiff",
    "image/jpeg",
}


@router.post("/validate", response_model=JobCreatedResponse, status_code=202)
async def upload_and_validate(
    file: UploadFile = File(...),
    client_locale: str = Form(default="pt-BR"),
    gramatura_gsm: int = Form(default=0),
    encadernacao: str = Form(default="none"),
    grain_direction: str = Form(default="unknown"),
    db: AsyncSession = Depends(get_db),
) -> JobCreatedResponse:
    """Receive a file for pre-flight validation via streaming upload.

    - Saves the file to disk using 8MB chunks (never loads entirely in RAM).
    - Creates a Job record with status QUEUED.
    - Dispatches the job to the Celery pipeline.
    - Returns 202 Accepted with a polling URL.
    """
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported Media Type: {file.content_type}. "
            f"Accepted: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Create directory for this job
    job_dir = Path(VOLUME_PATH) / job_id
    try:
        job_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HTTPException(
            status_code=507,
            detail=f"Insufficient Storage: {exc}",
        )

    # Save file via streaming (Rule 1: Anti-OOM — never load in memory)
    original_filename = file.filename or "upload.pdf"
    file_path = job_dir / original_filename
    file_size_bytes = 0

    import asyncio
    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                await asyncio.to_thread(f.write, chunk)
                file_size_bytes += len(chunk)
    except OSError as exc:
        raise HTTPException(
            status_code=507,
            detail=f"Insufficient Storage: {exc}",
        )

    # Create job record in database
    job = await create_job(
        db,
        job_id=job_id,
        original_filename=original_filename,
        file_path=str(file_path),
        file_size_bytes=file_size_bytes,
        client_locale=client_locale,
    )

    # Log event
    await create_event(
        db,
        job_id=job_id,
        agent_name="diretor",
        event_type="STATUS_CHANGE",
        event_level="INFO",
        payload=json.dumps({"from": None, "to": "QUEUED"}),
    )

    # Dispatch to Celery pipeline
    try:
        from workers.tasks import task_route

        job_payload = JobPayload(
            job_id=job_id,
            file_path=str(file_path),
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            submitted_at=datetime.now(timezone.utc),
            client_locale=client_locale,
        )
        task_route.delay(
            job_payload.model_dump_json(),
            json.dumps({
                "gramatura_gsm": gramatura_gsm,
                "encadernacao": encadernacao,
                "grain_direction": grain_direction,
            }),
        )
    except Exception as exc:
        # Log failure — Rule 4: Idempotency (job remains QUEUED for retry)
        import logging
        from workers.celery_app import CELERY_BROKER_URL
        logging.getLogger(__name__).error(f"Failed to dispatch job {job_id} to Celery (Broker: {CELERY_BROKER_URL}): {exc}")

    return JobCreatedResponse(
        job_id=job_id,
        status="QUEUED",
        polling_url=f"/api/v1/jobs/{job_id}/status",
        message="Arquivo recebido. Validação em andamento.",
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    """Poll job status."""
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        final_status=job.final_status,
        submitted_at=job.submitted_at,
        completed_at=job.completed_at,
        total_duration_ms=job.total_duration_ms,
        error_count=job.error_count,
        warning_count=job.warning_count,
    )


@router.get("/jobs/{job_id}/report", response_model=FinalReport)
async def get_job_report(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> FinalReport:
    """Retrieve the final validation report.

    Only available when the job status is DONE.
    """
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "DONE":
        raise HTTPException(
            status_code=409,
            detail=f"Report not ready. Current status: {job.status}",
        )

    # Build report from validation results
    results = await get_job_validation_results(db, job_id)

    erros = []
    avisos = []
    detalhes = {}

    for r in results:
        paginas: list[int] = []
        if r.pages_affected:
            try:
                parsed = json.loads(r.pages_affected)
                if isinstance(parsed, list):
                    for p in parsed:
                        try:
                            paginas.append(int(p))
                        except (TypeError, ValueError):
                            continue
            except (json.JSONDecodeError, TypeError, ValueError):
                paginas = []

        entry = {
            "codigo": r.error_code or r.check_code,
            "check_name": r.check_name,
            "found_value": r.value_found,
            "expected_value": r.value_expected,
        }
        if paginas:
            entry["paginas"] = paginas
        if r.status == "ERRO":
            entry["severidade"] = "CRÍTICO"
            erros.append(entry)
        elif r.status == "AVISO":
            entry["severidade"] = "AVISO"
            avisos.append(entry)

        row_detail: dict = {
            "status": r.status,
            "error_code": r.error_code,
            "found_value": r.value_found,
            "expected_value": r.value_expected,
        }
        if paginas:
            row_detail["paginas"] = paginas
        detalhes[r.check_code] = row_detail

    # Build summary text
    if job.final_status == "REPROVADO":
        resumo = (
            f"Foram encontrados {job.error_count} erro(s) crítico(s) que "
            f"impedem a impressão."
        )
    elif job.final_status == "APROVADO_COM_RESSALVAS":
        resumo = (
            f"Arquivo aprovado com {job.warning_count} aviso(s). "
            f"Revise os avisos para garantir o melhor resultado."
        )
    else:
        resumo = "Arquivo aprovado. Pronto para impressão."

    return FinalReport(
        job_id=job.id,
        status=job.final_status or "UNKNOWN",
        produto=job.detected_product or job.original_filename,
        agente_processador=job.processing_agent,
        avaliado_em=job.completed_at or datetime.now(timezone.utc),
        tempo_processamento_ms=job.total_duration_ms or 0,
        resumo=resumo,
        erros=erros,
        avisos=avisos,
        detalhes_tecnicos=detalhes,
    )


from fastapi.responses import FileResponse

@router.get("/jobs/{job_id}/file")
async def get_job_file(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Serve the original uploaded file for the PDF viewer."""
    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    file_path = Path(job.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=job.original_filename
    )
@router.get("/jobs/{job_id}/download-pdf")
async def download_job_report_pdf(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Generate and download the validation report as a PDF."""
    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "DONE":
        raise HTTPException(
            status_code=409, 
            detail=f"Report not ready. Current status: {job.status}"
        )

    results = await get_job_validation_results(db, job_id)
    
    # Generate PDF
    from app.utils.pdf_generator import AgenteGeradorPDF
    generator = AgenteGeradorPDF()
    
    report_filename = f"Relatorio_Validacao_{job_id[:8]}.pdf"
    job_dir = Path(VOLUME_PATH) / job_id
    report_path = job_dir / report_filename
    
    # Ensure directory exists (it should, but safety first)
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert ORM objects to dicts for the generator
    job_dict = {
        "id": job.id,
        "original_filename": job.original_filename,
        "file_size_bytes": job.file_size_bytes,
        "final_status": job.final_status,
        "detected_product": job.detected_product,
        "processing_agent": job.processing_agent
    }
    
    results_list = [
        {
            "check_code": r.check_code,
            "check_name": r.check_name,
            "status": r.status,
            "value_found": r.value_found,
            "value_expected": r.value_expected
        } 
        for r in results
    ]

    # Generate in a thread to keep the event loop free (fitz is sync)
    import asyncio
    await asyncio.to_thread(
        generator.gerar_relatorio, 
        job_dict, 
        results_list, 
        str(report_path)
    )
    
    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=report_filename
    )
