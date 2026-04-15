"""
Golden-rule tests — each remediator MUST fail (not silently degrade) when the
requested fix would cause quality loss. These assertions are load-bearing for
the industrial guarantee: a broken PDF never ships.
"""
from __future__ import annotations

from agentes.remediadores.color_space_remediator import ColorSpaceRemediator
from agentes.remediadores.font_remediator import FontRemediator
from agentes.remediadores.resolution_remediator import ResolutionRemediator
from app.api.schemas import ValidationResult


def test_font_remediator_rejects_courier_substitution(tmp_path):
    vr = ValidationResult(status="AVISO", codigo="W_COURIER_SUBSTITUTION",
                          found_value="Helvetica → Courier")
    action = FontRemediator().remediate(
        tmp_path / "in.pdf", tmp_path / "out.pdf", vr
    )
    assert action.success is False
    assert "Courier" in action.quality_loss_warnings[0]
    assert not (tmp_path / "out.pdf").exists()


def test_resolution_remediator_rejects_upsampling(tmp_path):
    # 150 dpi image < 300 dpi target → upsampling forbidden
    vr = ValidationResult(status="AVISO", codigo="W003_BORDERLINE_RESOLUTION",
                          found_value="Image at 150 dpi", expected_value="≥300 dpi")
    action = ResolutionRemediator().remediate(
        tmp_path / "in.pdf", tmp_path / "out.pdf", vr
    )
    assert action.success is False
    assert "upsampling is forbidden" in action.technical_log.lower()


def test_color_space_remediator_fails_when_icc_missing(tmp_path):
    vr = ValidationResult(status="REPROVADO", codigo="E006_FORBIDDEN_COLORSPACE",
                          found_value="RGB", expected_value="CMYK")
    remediator = ColorSpaceRemediator(icc_path=str(tmp_path / "missing.icc"))
    action = remediator.remediate(
        tmp_path / "in.pdf", tmp_path / "out.pdf", vr
    )
    assert action.success is False
    assert "ICC profile not found" in action.quality_loss_warnings[0]
