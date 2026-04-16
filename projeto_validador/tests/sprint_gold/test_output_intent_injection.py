"""
B-02 AC3 — Parameterized OutputIntent injection tests.

Exercises the 4 invalid states:
  1. absent          — /OutputIntents key missing entirely
  2. empty_array     — /OutputIntents = []
  3. wrong_subtype   — S entry ≠ /GTS_PDFX
  4. corrupt_profile — DestOutputProfile is 0 bytes

Plus the valid case (no-op): an already-correct OutputIntent must not be replaced.

Each invalid state is verified by:
  a) _detect_outputintent_state returning the expected string.
  b) After _inject_output_intent: pdfx_compliance.check_pdfx4() → is_compliant=True.
"""
from __future__ import annotations

import io
import struct
from pathlib import Path

import pytest

# pikepdf is a hard dependency for these tests
pikepdf = pytest.importorskip("pikepdf", reason="pikepdf required")

from agentes.remediadores.color_space_remediator import ColorSpaceRemediator
from agentes.validador_final.pdfx_compliance import check_pdfx4

# ── Helpers to build PDFs in each invalid state ──────────────────────────────

_ICC_PLACEHOLDER = b"\x00" * 512  # fake ICC — big enough to pass size check


def _simple_page(pdf):
    cs = pdf.make_stream(b"0 0.5 0.8 0.1 k 100 100 300 300 re f\n")
    obj = pdf.make_indirect(
        pikepdf.Dictionary(
            Type=pikepdf.Name("/Page"),
            MediaBox=pikepdf.Array([0, 0, 595, 842]),
            Contents=cs,
        )
    )
    return pikepdf.Page(obj)


def _make_pdf_absent(path: Path) -> None:
    """No /OutputIntents key at all."""
    pdf = pikepdf.new()
    pdf.pages.append(_simple_page(pdf))
    # Explicitly do NOT set OutputIntents
    pdf.save(path)


def _make_pdf_empty_array(path: Path) -> None:
    """/OutputIntents = []."""
    pdf = pikepdf.new()
    pdf.pages.append(_simple_page(pdf))
    pdf.Root.OutputIntents = pikepdf.Array([])
    pdf.save(path)


def _make_pdf_wrong_subtype(path: Path) -> None:
    """/S = /GTS_PDFA (wrong subtype)."""
    pdf = pikepdf.new()
    pdf.pages.append(_simple_page(pdf))
    icc = pdf.make_stream(_ICC_PLACEHOLDER)
    icc["/N"] = 4
    intent = pikepdf.Dictionary(
        Type=pikepdf.Name("/OutputIntent"),
        S=pikepdf.Name("/GTS_PDFA"),  # wrong
        OutputConditionIdentifier=pikepdf.String("sRGB"),
        DestOutputProfile=icc,
    )
    pdf.Root.OutputIntents = pikepdf.Array([intent])
    pdf.save(path)


def _make_pdf_corrupt_profile(path: Path) -> None:
    """DestOutputProfile is 0 bytes (corrupt)."""
    pdf = pikepdf.new()
    pdf.pages.append(_simple_page(pdf))
    empty_icc = pdf.make_stream(b"")  # 0-byte profile
    intent = pikepdf.Dictionary(
        Type=pikepdf.Name("/OutputIntent"),
        S=pikepdf.Name("/GTS_PDFX"),
        OutputConditionIdentifier=pikepdf.String("FOGRA39"),
        DestOutputProfile=empty_icc,
    )
    pdf.Root.OutputIntents = pikepdf.Array([intent])
    pdf.save(path)


def _make_pdf_valid(path: Path) -> None:
    """A valid GTS_PDFX OutputIntent with a large-enough ICC profile."""
    pdf = pikepdf.new()
    pdf.pages.append(_simple_page(pdf))
    icc = pdf.make_stream(_ICC_PLACEHOLDER)
    icc["/N"] = 4
    intent = pikepdf.Dictionary(
        Type=pikepdf.Name("/OutputIntent"),
        S=pikepdf.Name("/GTS_PDFX"),
        OutputConditionIdentifier=pikepdf.String("FOGRA39"),
        RegistryName=pikepdf.String("http://www.color.org"),
        Info=pikepdf.String("Coated FOGRA39 (ISO 12647-2:2004)"),
        DestOutputProfile=icc,
    )
    pdf.Root.OutputIntents = pikepdf.Array([intent])
    pdf.Root.GTS_PDFXVersion = pikepdf.String("PDF/X-4")
    pdf.save(path)


# ── State detection tests ────────────────────────────────────────────────────

@pytest.mark.parametrize("builder,expected_state", [
    (_make_pdf_absent, "absent"),
    (_make_pdf_empty_array, "empty_array"),
    (_make_pdf_wrong_subtype, "wrong_subtype"),
    (_make_pdf_corrupt_profile, "corrupt_profile"),
    (_make_pdf_valid, "valid"),
])
def test_detect_outputintent_state(tmp_path, builder, expected_state):
    """B-02 AC1: _detect_outputintent_state correctly classifies all 4 invalid states."""
    pdf_path = tmp_path / f"test_{expected_state}.pdf"
    builder(pdf_path)

    fake_icc = tmp_path / "fake.icc"
    fake_icc.write_bytes(_ICC_PLACEHOLDER)

    remediator = ColorSpaceRemediator(icc_path=str(fake_icc))
    state = remediator._detect_outputintent_state(pdf_path)
    assert state == expected_state, f"Expected state={expected_state!r}, got {state!r}"


# ── Injection post-condition: is_compliant=True ──────────────────────────────

@pytest.mark.parametrize("builder,state_label", [
    (_make_pdf_absent, "absent"),
    (_make_pdf_empty_array, "empty_array"),
    (_make_pdf_wrong_subtype, "wrong_subtype"),
    (_make_pdf_corrupt_profile, "corrupt_profile"),
])
def test_inject_output_intent_makes_compliant(tmp_path, builder, state_label):
    """B-02 AC2+AC4: after _inject_output_intent, check_pdfx4() → is_compliant=True."""
    pdf_path = tmp_path / f"{state_label}.pdf"
    builder(pdf_path)

    fake_icc = tmp_path / "real.icc"
    fake_icc.write_bytes(_ICC_PLACEHOLDER)

    remediator = ColorSpaceRemediator(icc_path=str(fake_icc))
    remediator._inject_output_intent(pdf_path)

    result = check_pdfx4(pdf_path)
    assert result["is_compliant"] is True, (
        f"PDF not compliant after injection for state={state_label!r}: "
        f"{result['errors']}"
    )
    assert result["output_intent_subtype"] == "/GTS_PDFX"
    assert result["has_output_profile"] is True


def test_inject_output_intent_noop_for_valid_state(tmp_path):
    """B-02 AC1 (valid no-op): a valid OutputIntent must NOT be replaced."""
    pdf_path = tmp_path / "valid.pdf"
    _make_pdf_valid(pdf_path)

    # Record the original OutputIntent identifier
    with pikepdf.open(pdf_path) as pdf:
        original_ident = str(pdf.Root.OutputIntents[0]["/OutputConditionIdentifier"])

    fake_icc = tmp_path / "real.icc"
    fake_icc.write_bytes(_ICC_PLACEHOLDER)

    remediator = ColorSpaceRemediator(icc_path=str(fake_icc))
    remediator._inject_output_intent(pdf_path)

    # OutputIntent must still be there, unchanged
    with pikepdf.open(pdf_path) as pdf:
        after_ident = str(pdf.Root.OutputIntents[0]["/OutputConditionIdentifier"])

    assert after_ident == original_ident, (
        "Valid OutputIntent was unexpectedly replaced (no-op violated)"
    )


# ── Full E_OUTPUTINTENT_MISSING remediation path ────────────────────────────

@pytest.mark.parametrize("builder,state_label", [
    (_make_pdf_absent, "absent"),
    (_make_pdf_empty_array, "empty_array"),
    (_make_pdf_wrong_subtype, "wrong_subtype"),
    (_make_pdf_corrupt_profile, "corrupt_profile"),
])
def test_remediate_outputintent_missing_end_to_end(tmp_path, builder, state_label):
    """B-02 full path: remediate(E_OUTPUTINTENT_MISSING) produces compliant PDF."""
    from app.api.schemas import ValidationResult

    src = tmp_path / f"src_{state_label}.pdf"
    dst = tmp_path / f"dst_{state_label}.pdf"
    builder(src)

    fake_icc = tmp_path / "fogra39.icc"
    fake_icc.write_bytes(_ICC_PLACEHOLDER)

    vr = ValidationResult(
        status="REPROVADO",
        codigo="E_OUTPUTINTENT_MISSING",
        found_value=state_label,
    )
    remediator = ColorSpaceRemediator(icc_path=str(fake_icc))
    action = remediator.remediate(src, dst, vr)

    assert action.success is True, (
        f"remediate failed for state={state_label!r}: {action.quality_loss_warnings}"
    )
    assert dst.exists()
    result = check_pdfx4(dst)
    assert result["is_compliant"] is True, (
        f"PDF not compliant after full remediation for state={state_label!r}: "
        f"{result['errors']}"
    )


def test_remediate_fails_gracefully_when_icc_missing(tmp_path):
    """B-02: when ICC is not on disk, remediation returns success=False (no silent fallback)."""
    from app.api.schemas import ValidationResult

    src = tmp_path / "src.pdf"
    _make_pdf_absent(src)
    dst = tmp_path / "dst.pdf"

    vr = ValidationResult(status="REPROVADO", codigo="E_OUTPUTINTENT_MISSING")
    remediator = ColorSpaceRemediator(icc_path=str(tmp_path / "nonexistent.icc"))
    action = remediator.remediate(src, dst, vr)

    assert action.success is False
    assert any("ICC" in w for w in action.quality_loss_warnings)
