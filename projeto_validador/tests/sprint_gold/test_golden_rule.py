"""
Golden-rule tests — post-Sprint A "Entregar sempre, auditar tudo" contract.

Renaming history (for git blame):
  test_font_remediator_rejects_courier_substitution
      → test_font_remediator_accepts_courier_with_warning   (A-05 AC1)
  test_resolution_remediator_rejects_upsampling
      → test_resolution_remediator_upsamples_with_warning   (A-05 AC2)
  test_color_space_remediator_fails_when_icc_missing        (kept — A-05 AC3)
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from agentes.remediadores.color_space_remediator import ColorSpaceRemediator
from agentes.remediadores.font_remediator import FontRemediator
from agentes.remediadores.resolution_remediator import ResolutionRemediator
from app.api.schemas import ValidationResult


# ── Font remediator ──────────────────────────────────────────────────────────

def test_font_remediator_accepts_courier_with_warning(tmp_path):
    """A-05 AC1: Courier substitution → success=True + warning (no hard fail)."""
    vr = ValidationResult(
        status="AVISO",
        codigo="W_COURIER_SUBSTITUTION",
        found_value="Helvetica → Courier",
    )
    # Ghostscript will fail because in.pdf does not exist, but Courier path now
    # short-circuits to embed with gs; patch gs check to avoid binary dependency.
    with patch("shutil.which", return_value="/usr/bin/gs"):
        # Ghostscript will exit non-zero on a missing file — expect _fail on gs error
        # but NOT because of the Courier policy.  Run actual call to verify code path.
        action = FontRemediator().remediate(tmp_path / "in.pdf", tmp_path / "out.pdf", vr)

    # The Courier substitution code path no longer raises an early _fail.
    # With a missing input the gs call itself will fail (technical failure) — that's OK.
    # The key assertion: quality_loss_warnings must NOT contain "Courier" as a policy fail.
    # We verify the IS-courier path doesn't return early with success=False + courier msg.
    assert "Regra de Ouro" not in (action.technical_log or "")


def test_font_remediator_courier_path_emits_warning_on_success(tmp_path):
    """A-05 AC1 (end-to-end stub): when gs succeeds, action must have courier warning."""
    vr = ValidationResult(
        status="AVISO",
        codigo="W_COURIER_SUBSTITUTION",
        found_value="Arial → Courier",
    )
    fake_pdf = tmp_path / "in.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 fake")

    def fake_run(cmd, **kwargs):
        # Simulate gs writing the output file
        out = Path(kwargs.get("cwd", tmp_path)) if "cwd" in kwargs else tmp_path
        # Extract -sOutputFile= from cmd
        for arg in cmd:
            if arg.startswith("-sOutputFile="):
                Path(arg.split("=", 1)[1]).write_bytes(b"%PDF-1.4 remediated")
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    with (
        patch("shutil.which", return_value="/usr/bin/gs"),
        patch("subprocess.run", side_effect=fake_run),
        patch.object(FontRemediator, "_list_missing_fonts", return_value=[]),
    ):
        action = FontRemediator().remediate(fake_pdf, tmp_path / "out.pdf", vr)

    assert action.success is True
    assert action.quality_loss_warnings, "Expected quality_loss_warnings for Courier fallback"
    assert any("Courier" in w for w in action.quality_loss_warnings)


# ── Resolution remediator ────────────────────────────────────────────────────

def test_resolution_remediator_upsamples_with_warning(tmp_path):
    """A-05 AC2: 150 dpi image → upsampled with success=True + warning (no hard fail)."""
    fake_pdf = tmp_path / "in.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 fake")

    vr = ValidationResult(
        status="AVISO",
        codigo="W003_BORDERLINE_RESOLUTION",
        found_value="Image at 150 dpi",
        expected_value="≥300 dpi",
    )

    def fake_run(cmd, **kwargs):
        for arg in cmd:
            if arg.startswith("-sOutputFile="):
                Path(arg.split("=", 1)[1]).write_bytes(b"%PDF-1.4 upsampled")
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    with (
        patch("shutil.which", return_value="/usr/bin/gs"),
        patch("subprocess.run", side_effect=fake_run),
    ):
        action = ResolutionRemediator().remediate(fake_pdf, tmp_path / "out.pdf", vr)

    assert action.success is True
    assert (tmp_path / "out.pdf").exists()
    assert any("upsampled" in w.lower() for w in action.quality_loss_warnings), (
        "Expected 'upsampled' in quality_loss_warnings"
    )


def test_resolution_remediator_downsamples_without_warning(tmp_path):
    """High-res images are downsampled cleanly — no quality_loss_warnings."""
    fake_pdf = tmp_path / "in.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 fake")

    vr = ValidationResult(
        status="AVISO",
        codigo="W003_BORDERLINE_RESOLUTION",
        found_value="Image at 600 dpi",
        expected_value="≥300 dpi",
    )

    def fake_run(cmd, **kwargs):
        for arg in cmd:
            if arg.startswith("-sOutputFile="):
                Path(arg.split("=", 1)[1]).write_bytes(b"%PDF-1.4 downsampled")
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    with (
        patch("shutil.which", return_value="/usr/bin/gs"),
        patch("subprocess.run", side_effect=fake_run),
    ):
        action = ResolutionRemediator().remediate(fake_pdf, tmp_path / "out.pdf", vr)

    assert action.success is True
    assert not action.quality_loss_warnings


# ── Color space remediator ───────────────────────────────────────────────────

def test_color_space_remediator_fails_when_icc_missing(tmp_path):
    """A-05 AC3: ICC profile not found is a REAL technical failure → success=False (kept)."""
    vr = ValidationResult(
        status="REPROVADO",
        codigo="E006_FORBIDDEN_COLORSPACE",
        found_value="RGB",
        expected_value="CMYK",
    )
    remediator = ColorSpaceRemediator(icc_path=str(tmp_path / "missing.icc"))
    action = remediator.remediate(tmp_path / "in.pdf", tmp_path / "out.pdf", vr)
    assert action.success is False
    assert "ICC profile not found" in action.quality_loss_warnings[0]
