"""
Sprint C — VeraPDF attestation PDF generator.

Produces a single-page PDF attestation from a VeraPDFReport using PyMuPDF (fitz).
No extra dependencies beyond what is already in requirements.txt.
"""
from __future__ import annotations

from datetime import datetime, timezone

import fitz  # PyMuPDF

from app.api.schemas import VeraPDFReport

# ── Design tokens (aligned with AgenteGeradorPDF palette) ────────────────────
_BLACK = (0.04, 0.04, 0.06)
_WHITE = (1.0, 1.0, 1.0)
_GREEN = (0.06, 0.73, 0.51)
_RED = (0.94, 0.27, 0.27)
_BLUE = (0.23, 0.51, 0.96)
_GREY = (0.39, 0.45, 0.55)
_SOFT = (0.96, 0.97, 0.98)


def generate_attestation_pdf(
    report: VeraPDFReport,
    original_filename: str,
    output_path: str,
) -> str:
    """Write a VeraPDF attestation PDF to *output_path* and return that path."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    W, H = page.rect.width, page.rect.height

    # ── Header bar ────────────────────────────────────────────────────────────
    page.draw_rect(fitz.Rect(0, 0, W, 90), color=None, fill=_BLACK)
    page.insert_text(
        (30, 40),
        "ATESTADO DE CONFORMIDADE PDF/X-4",
        fontsize=18,
        color=_WHITE,
        fontname="Helvetica-Bold",
    )
    page.insert_text(
        (30, 65),
        "Graphic-Pro Preflight Validation System — Sprint C VeraPDF",
        fontsize=9,
        color=(0.7, 0.7, 0.7),
        fontname="Helvetica",
    )

    # ── Status badge ─────────────────────────────────────────────────────────
    badge_color = _GREEN if report.passed else _RED
    badge_text = "APROVADO  PDF/X-4" if report.passed else "REPROVADO  PDF/X-4"
    page.draw_rect(fitz.Rect(30, 105, W - 30, 145), color=None, fill=badge_color)
    page.insert_text(
        (40, 131),
        badge_text,
        fontsize=16,
        color=_WHITE,
        fontname="Helvetica-Bold",
    )

    # ── Metadata table ────────────────────────────────────────────────────────
    y = 165
    rows = [
        ("Job ID", report.job_id),
        ("Arquivo", original_filename),
        ("Perfil validado", report.profile or "PDF/X-4"),
        (
            "Data / Hora",
            report.timestamp.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC"),
        ),
        ("Violações detectadas", str(len(report.rule_violations))),
    ]
    page.insert_text(
        (30, y), "DETALHES DO JOB", fontsize=11, color=_BLACK, fontname="Helvetica-Bold"
    )
    y += 18
    for label, value in rows:
        page.insert_text((30, y), f"{label}:", fontsize=9, color=_GREY, fontname="Helvetica-Bold")
        page.insert_text((160, y), value, fontsize=9, color=_BLACK, fontname="Helvetica")
        y += 16

    # ── Violations table ──────────────────────────────────────────────────────
    y += 10
    page.insert_text(
        (30, y), "VIOLAÇÕES DE REGRA", fontsize=11, color=_BLACK, fontname="Helvetica-Bold"
    )
    y += 18

    if not report.rule_violations:
        page.insert_text(
            (30, y),
            "Nenhuma violação detectada — documento em conformidade total.",
            fontsize=9,
            color=_GREEN,
            fontname="Helvetica",
        )
        y += 20
    else:
        # Column headers
        page.draw_rect(fitz.Rect(30, y - 12, W - 30, y + 4), color=None, fill=_SOFT)
        page.insert_text((32, y), "Regra", fontsize=8, color=_BLACK, fontname="Helvetica-Bold")
        page.insert_text((100, y), "Objeto", fontsize=8, color=_BLACK, fontname="Helvetica-Bold")
        page.insert_text((200, y), "Falhas", fontsize=8, color=_BLACK, fontname="Helvetica-Bold")
        page.insert_text((250, y), "Descrição", fontsize=8, color=_BLACK, fontname="Helvetica-Bold")
        y += 16

        for v in report.rule_violations[:30]:  # cap at 30 rows for space
            desc = v.description[:55] + "…" if len(v.description) > 55 else v.description
            page.insert_text((32, y), v.rule_id, fontsize=8, color=_RED, fontname="Helvetica")
            page.insert_text((100, y), (v.object_type or "-")[:12], fontsize=8, color=_BLACK)
            page.insert_text((200, y), str(v.failed_count), fontsize=8, color=_RED)
            page.insert_text((250, y), desc, fontsize=8, color=_BLACK)
            y += 14
            if y > H - 80:
                break

        if len(report.rule_violations) > 30:
            page.insert_text(
                (30, y + 4),
                f"… e mais {len(report.rule_violations) - 30} violações (ver JSON completo).",
                fontsize=8,
                color=_GREY,
            )
            y += 20

    # ── Footer ────────────────────────────────────────────────────────────────
    page.draw_rect(fitz.Rect(0, H - 40, W, H), color=None, fill=_BLACK)
    page.insert_text(
        (30, H - 18),
        "Gerado automaticamente por Graphic-Pro · "
        + datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        fontsize=8,
        color=(0.6, 0.6, 0.6),
        fontname="Helvetica",
    )
    page.insert_text(
        (W - 180, H - 18),
        "VeraPDF — referência industrial PDF/X-4",
        fontsize=8,
        color=(0.6, 0.6, 0.6),
        fontname="Helvetica",
    )

    doc.save(output_path)
    doc.close()
    return output_path
