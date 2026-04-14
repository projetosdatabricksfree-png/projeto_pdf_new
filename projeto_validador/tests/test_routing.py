"""
Tests for the routing logic (Gerente agent).
"""
from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentes.gerente.agent import classificar_produto, THRESHOLD_CONFIANCA


class TestClassificarProduto:
    """Tests for the geometric classification function."""

    def test_papelaria_plana_cartao_visita(self):
        """Small area + ≤2 pages → papelaria plana."""
        meta = {"width_mm": 85.6, "height_mm": 53.98, "page_count": 1}
        route, conf, reason = classificar_produto(meta)
        assert route == "operario_papelaria_plana"
        assert conf >= THRESHOLD_CONFIANCA

    def test_projetos_cad_a0(self):
        """Large format (≥420mm) → projetos CAD."""
        meta = {"width_mm": 841, "height_mm": 1189, "page_count": 1}
        route, conf, reason = classificar_produto(meta)
        assert route == "operario_projetos_cad"
        assert conf >= THRESHOLD_CONFIANCA

    def test_projetos_cad_a2(self):
        """A2 format → projetos CAD."""
        meta = {"width_mm": 420, "height_mm": 594, "page_count": 1}
        route, conf, reason = classificar_produto(meta)
        assert route == "operario_projetos_cad"

    def test_editoriais_many_pages(self):
        """≥8 pages → editoriais."""
        meta = {"width_mm": 210, "height_mm": 297, "page_count": 20}
        route, conf, reason = classificar_produto(meta)
        assert route == "operario_editoriais"
        assert conf >= THRESHOLD_CONFIANCA

    def test_editoriais_8_pages(self):
        """Exactly 8 pages → editoriais (lower confidence)."""
        meta = {"width_mm": 210, "height_mm": 297, "page_count": 8}
        route, conf, reason = classificar_produto(meta)
        assert route == "operario_editoriais"
        assert conf >= THRESHOLD_CONFIANCA

    def test_dobraduras_trifold(self):
        """3 pages → dobraduras."""
        meta = {"width_mm": 297, "height_mm": 210, "page_count": 3}
        route, conf, reason = classificar_produto(meta)
        assert route == "operario_dobraduras"

    def test_dobraduras_panoramic_ratio(self):
        """High width/height ratio → dobraduras."""
        meta = {"width_mm": 400, "height_mm": 200, "page_count": 1}
        route, conf, reason = classificar_produto(meta)
        assert route == "operario_dobraduras"

    def test_cortes_especiais_small_irregular(self):
        """Small area + ≤4 pages (not papelaria) → cortes especiais."""
        meta = {"width_mm": 100, "height_mm": 80, "page_count": 1}
        route, conf, reason = classificar_produto(meta)
        assert route == "operario_cortes_especiais"

    def test_ambiguous_routes_to_especialista(self):
        """Ambiguous case → especialista with low confidence."""
        meta = {"width_mm": 300, "height_mm": 300, "page_count": 5}
        route, conf, reason = classificar_produto(meta)
        assert route == "especialista"
        assert conf < THRESHOLD_CONFIANCA

    def test_low_confidence_triggers_specialist(self):
        """Confidence below threshold should flag for specialist."""
        meta = {"width_mm": 100, "height_mm": 80, "page_count": 1}
        _, conf, _ = classificar_produto(meta)
        assert conf < THRESHOLD_CONFIANCA  # cortes_especiais returns 0.82

    def test_exiftool_failure_routes_to_specialist(self):
        """When metadata extraction fails, should route to especialista."""
        from app.api.schemas import JobPayload
        from agentes.gerente.agent import AgenteGerente
        from datetime import datetime, timezone

        gerente = AgenteGerente()
        payload = JobPayload(
            job_id="test-123",
            file_path="/nonexistent/file.pdf",
            original_filename="test.pdf",
            file_size_bytes=1000,
            submitted_at=datetime.now(timezone.utc),
        )
        result = gerente.processar(payload)
        assert result.route_to == "especialista"
        assert result.confidence == 0.0
        assert result.reason == "METADATA_EXTRACTION_FAILED"
