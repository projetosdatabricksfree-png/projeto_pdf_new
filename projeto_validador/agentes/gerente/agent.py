"""
Agente Gerente — Routing agent with geometric classification.

Consumes jobs from queue:jobs, extracts lightweight metadata via ExifTool,
and routes to the correct Operário based on dimensions and page count.

Classification logic matches EXACTLY the specification in PROMPT_IMPLEMENTACAO.md.
"""
from __future__ import annotations

import logging

from app.api.schemas import JobPayload, RoutingPayload

logger = logging.getLogger(__name__)

# Confidence threshold — below this, the Especialista is called
THRESHOLD_CONFIANCA: float = 0.85


def classificar_produto(metadata: dict) -> tuple[str, float, str]:
    """Classify the product type based on geometric metadata.

    This logic is EXACTLY as specified in the prompt — do not modify.

    Args:
        metadata: Dictionary with width_mm, height_mm, page_count.

    Returns:
        Tuple of (operario_name, confidence_score, reason).
    """
    width_mm: float = metadata.get("width_mm", 0)
    height_mm: float = metadata.get("height_mm", 0)
    pages: int = metadata.get("page_count", 1)
    area: float = width_mm * height_mm
    ratio: float = max(width_mm, height_mm) / max(min(width_mm, height_mm), 1)

    # Projetos CAD — grandes formatos
    if width_mm >= 420 or height_mm >= 420:
        return ("operario_projetos_cad", 0.93, "LARGE_FORMAT_CAD")

    # Papelaria plana — formatos de cartão
    if area < 6000 and pages <= 2:
        return ("operario_papelaria_plana", 0.95, "SMALL_FORMAT_CARD")

    # Editorial — muitas páginas
    if pages >= 8:
        confidence = 0.96 if pages >= 20 else 0.88
        return ("operario_editoriais", confidence, "MULTIPAGE_EDITORIAL")

    # Dobraduras — multipáginas panorâmicas ou proporcional
    if pages in [2, 3, 4, 6] or ratio > 1.8:
        return ("operario_dobraduras", 0.87, "PANORAMIC_FOLD")

    # Cortes especiais — formatos pequenos irregulares
    if area < 12000 and pages <= 4:
        return ("operario_cortes_especiais", 0.82, "SMALL_IRREGULAR_CUT")

    # Ambíguo → Especialista
    return ("especialista", 0.50, "AMBIGUOUS_GEOMETRY")


class AgenteGerente:
    """Routing agent that classifies files and dispatches to operários."""

    def processar(
        self,
        job_payload: JobPayload,
        job_metadata: dict | None = None,
    ) -> RoutingPayload:
        """Process a job: extract metadata, classify, and create routing payload.

        Args:
            job_payload: The job payload from the Diretor.
            job_metadata: Extra metadata (gramatura, encadernação, etc.)

        Returns:
            RoutingPayload with routing decision.
        """
        job_metadata = job_metadata or {}
        metadata_snapshot: dict = {}
        alerts: list[dict] = []

        # Step 1: Try ExifTool metadata extraction
        try:
            from agentes.gerente.tools.exiftool_reader import (
                detect_pre_routing_alerts,
                extract_dimensions_mm,
                extract_metadata,
                get_page_count,
            )

            raw_metadata = extract_metadata(job_payload.file_path)
            width_mm, height_mm = extract_dimensions_mm(raw_metadata)
            page_count = get_page_count(raw_metadata)
            alerts = detect_pre_routing_alerts(raw_metadata)

            # ExifTool succeeds mas frequentemente devolve 0x0 mm para PDFs.
            # Preenche com PyMuPDF (page.mediabox em pontos → mm) para nunca
            # chegar zerado no roteamento.
            dim_source = "exiftool"
            if width_mm <= 0 or height_mm <= 0:
                try:
                    w2, h2, p2 = self._fallback_pymupdf(job_payload.file_path)
                    if w2 > 0 and h2 > 0:
                        width_mm, height_mm = w2, h2
                        if page_count <= 0:
                            page_count = p2
                        dim_source = "exiftool+pymupdf"
                        logger.info(
                            f"[Gerente] ExifTool retornou 0mm — dimensões "
                            f"preenchidas via PyMuPDF: {width_mm}x{height_mm}mm"
                        )
                except Exception as exc:
                    logger.warning(f"[Gerente] PyMuPDF dim fallback falhou: {exc}")

            metadata_snapshot = {
                "width_mm": width_mm,
                "height_mm": height_mm,
                "page_count": page_count,
                "dim_source": dim_source,
                "raw": {k: str(v) for k, v in raw_metadata.items()},
                "alerts": alerts,
            }

        except (RuntimeError, FileNotFoundError) as exc:
            # ExifTool failed → fallback to Especialista
            logger.warning(
                f"[Gerente] ExifTool failed for job {job_payload.job_id}: {exc}"
            )

            # Try PyMuPDF as fallback for PDFs
            try:
                width_mm, height_mm, page_count = self._fallback_pymupdf(
                    job_payload.file_path
                )
                metadata_snapshot = {
                    "width_mm": width_mm,
                    "height_mm": height_mm,
                    "page_count": page_count,
                    "source": "pymupdf_fallback",
                }
            except Exception:
                return RoutingPayload(
                    job_id=job_payload.job_id,
                    file_path=job_payload.file_path,
                    file_size_bytes=job_payload.file_size_bytes,
                    route_to="especialista",
                    confidence=0.0,
                    reason="METADATA_EXTRACTION_FAILED",
                    metadata_snapshot=metadata_snapshot,
                    client_locale=job_payload.client_locale,
                    job_metadata=job_metadata,
                )

        # Step 2: Classify product
        classify_meta = {
            "width_mm": metadata_snapshot.get("width_mm", 0),
            "height_mm": metadata_snapshot.get("height_mm", 0),
            "page_count": metadata_snapshot.get("page_count", 1),
        }

        # Uses purely deterministic geometric routing logic
        route_to, confidence, reason = classificar_produto(classify_meta)

        # Step 3: If confidence below threshold, route to Especialista
        if confidence < THRESHOLD_CONFIANCA and route_to != "especialista":
            logger.info(
                f"[Gerente] Low confidence ({confidence}) for job "
                f"{job_payload.job_id} → routing to especialista"
            )

            # Try specialist for refined routing
            try:
                from agentes.especialista.agent import AgenteEspecialista

                especialista = AgenteEspecialista()
                specialist_result = especialista.processar(
                    job_payload.file_path,
                    metadata_snapshot,
                )
                route_to = specialist_result["route_to"]
                confidence = specialist_result["confidence"]
                reason = specialist_result["reason"]
            except Exception as exc:
                logger.error(f"[Gerente] Specialist failed: {exc}")
                # Keep original low-confidence routing

        logger.info(
            f"[Gerente] Job {job_payload.job_id} → {route_to} "
            f"(confidence={confidence}, reason={reason})"
        )

        # Mapping reasons to human product names for GWG profile selection
        product_map = {
            "LARGE_FORMAT_CAD": "Projeto CAD",
            "SMALL_FORMAT_CARD": "Papelaria Plana",
            "MULTIPAGE_EDITORIAL": "Editorial",
            "PANORAMIC_FOLD": "Dobraduras",
            "SMALL_IRREGULAR_CUT": "Cortes Especiais",
        }
        detected_p = product_map.get(reason, "Digital / Genérico")

        return RoutingPayload(
            job_id=job_payload.job_id,
            file_path=job_payload.file_path,
            file_size_bytes=job_payload.file_size_bytes,
            route_to=route_to,
            confidence=confidence,
            reason=reason,
            metadata_snapshot=metadata_snapshot,
            client_locale=job_payload.client_locale,
            job_metadata=job_metadata,
            produto_detectado=detected_p
        )

    @staticmethod
    def _fallback_pymupdf(file_path: str) -> tuple[float, float, int]:
        """Fallback metadata extraction via PyMuPDF when ExifTool fails.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Tuple of (width_mm, height_mm, page_count).
        """
        import fitz

        doc = fitz.open(file_path)
        try:
            page = doc[0]
            rect = page.mediabox
            width_mm = round(rect.width * 25.4 / 72, 2)
            height_mm = round(rect.height * 25.4 / 72, 2)
            page_count = doc.page_count
            return width_mm, height_mm, page_count
        finally:
            doc.close()
