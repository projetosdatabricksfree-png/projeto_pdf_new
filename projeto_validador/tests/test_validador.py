"""
Tests for the Validador agent (deterministic report engine).
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentes.validador.agent import AgenteValidador, calcular_status_final
from agentes.validador.messages_table import get_message, MESSAGES
from app.api.schemas import TechnicalReport
from datetime import datetime, timezone


class TestCalcularStatusFinal:
    """Tests for the deterministic status calculation."""

    def test_errors_means_reprovado(self):
        """Any E-prefixed code → REPROVADO."""
        assert calcular_status_final(["E002_MISSING_BLEED"], []) == "REPROVADO"

    def test_multiple_errors_means_reprovado(self):
        """Multiple errors → still REPROVADO."""
        assert calcular_status_final(
            ["E002_MISSING_BLEED", "E006_RGB_COLORSPACE"], []
        ) == "REPROVADO"

    def test_only_warnings_means_aprovado_com_ressalvas(self):
        """Only W-prefixed codes → APROVADO_COM_RESSALVAS."""
        assert calcular_status_final([], ["W001_EXCESSIVE_BLEED"]) == "APROVADO_COM_RESSALVAS"

    def test_no_errors_no_warnings_means_aprovado(self):
        """No codes → APROVADO."""
        assert calcular_status_final([], []) == "APROVADO"

    def test_errors_and_warnings_means_reprovado(self):
        """Errors trump warnings → REPROVADO."""
        assert calcular_status_final(
            ["E002_MISSING_BLEED"], ["W001_EXCESSIVE_BLEED"]
        ) == "REPROVADO"

    def test_non_e_prefixed_not_counted(self):
        """Non-E-prefixed items in errors don't trigger REPROVADO."""
        assert calcular_status_final(["INFO_SOMETHING"], []) == "APROVADO"


class TestGetMessage:
    """Tests for the localized message retrieval."""

    def test_ptbr_message_exists(self):
        """pt-BR messages should be complete."""
        msg = get_message("E002_MISSING_BLEED", "pt-BR")
        assert "titulo" in msg
        assert "descricao" in msg
        assert "acao" in msg
        assert "Sangria" in msg["titulo"]

    def test_enus_message_exists(self):
        """en-US messages should be available."""
        msg = get_message("E002_MISSING_BLEED", "en-US")
        assert "Bleed" in msg["titulo"]

    def test_eses_message_exists(self):
        """es-ES messages should be available."""
        msg = get_message("E002_MISSING_BLEED", "es-ES")
        assert "Sangrado" in msg["titulo"]

    def test_unknown_code_fallback(self):
        """Unknown codes should return a generic message."""
        msg = get_message("UNKNOWN_CODE_XYZ", "pt-BR")
        assert "titulo" in msg
        assert "UNKNOWN_CODE_XYZ" in msg["titulo"]

    def test_unknown_locale_fallback_to_ptbr(self):
        """Unknown locale should fallback to pt-BR."""
        msg = get_message("E002_MISSING_BLEED", "fr-FR")
        assert "Sangria" in msg["titulo"]


class TestAgenteValidador:
    """Tests for the Validador agent processing."""

    def _make_report(self, erros=None, avisos=None) -> TechnicalReport:
        return TechnicalReport(
            job_id="test-123",
            agent="operario_papelaria_plana",
            produto_detectado="Cartão de Visita",
            status="",
            erros_criticos=erros or [],
            avisos=avisos or [],
            validation_results={},
            processing_time_ms=100,
            timestamp=datetime.now(timezone.utc),
        )

    def test_reprovado_report(self):
        """Report with errors should produce REPROVADO."""
        validador = AgenteValidador()
        report = self._make_report(erros=["E002_MISSING_BLEED"])
        final = validador.processar(report)

        assert final.status == "REPROVADO"
        assert len(final.erros) == 1
        assert final.erros[0]["codigo"] == "E002_MISSING_BLEED"

    def test_aprovado_com_ressalvas_report(self):
        """Report with only warnings should produce APROVADO_COM_RESSALVAS."""
        validador = AgenteValidador()
        report = self._make_report(avisos=["W001_EXCESSIVE_BLEED"])
        final = validador.processar(report)

        assert final.status == "APROVADO_COM_RESSALVAS"
        assert len(final.avisos) == 1

    def test_aprovado_report(self):
        """Clean report should produce APROVADO."""
        validador = AgenteValidador()
        report = self._make_report()
        final = validador.processar(report)

        assert final.status == "APROVADO"
        assert len(final.erros) == 0
        assert len(final.avisos) == 0

    def test_ptbr_locale(self):
        """Should produce pt-BR messages by default."""
        validador = AgenteValidador()
        report = self._make_report(erros=["E002_MISSING_BLEED"])
        final = validador.processar(report, locale="pt-BR")

        assert "REPROVADO" in final.resumo
        assert "Sangria" in final.erros[0]["titulo"]

    def test_enus_locale(self):
        """Should produce en-US messages when requested."""
        validador = AgenteValidador()
        report = self._make_report(erros=["E002_MISSING_BLEED"])
        final = validador.processar(report, locale="en-US")

        assert "RESULT" in final.resumo
        assert "Bleed" in final.erros[0]["titulo"]

    def test_eses_locale(self):
        """Should produce es-ES messages when requested."""
        validador = AgenteValidador()
        report = self._make_report(erros=["E002_MISSING_BLEED"])
        final = validador.processar(report, locale="es-ES")

        assert "RESULTADO" in final.resumo
