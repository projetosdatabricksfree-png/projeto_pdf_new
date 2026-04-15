"""
Base contract for all remediators.

Remediators are deterministic: given a PDF and a specific ValidationResult node,
they produce a new PDF (or fail cleanly) and a RemediationAction describing what
changed. They never use LLMs, never guess, and never upsample/invent data.

Regra de Ouro: if the fix would cause quality loss (font substitution, upsampling,
destructive flattening), the remediator MUST fail and emit a technical_log so the
validador_final can reject the job.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.api.schemas import RemediationAction, ValidationResult

logger = logging.getLogger(__name__)


class RemediatorError(Exception):
    """Raised when a remediator cannot fix an error without quality loss."""


class BaseRemediator(ABC):
    """Abstract base for all Gold-layer remediators."""

    #: Human-readable name, e.g. "ColorSpaceRemediator".
    name: str = "BaseRemediator"

    #: Error codes this remediator handles (populated by subclasses).
    handles: tuple[str, ...] = ()

    @abstractmethod
    def remediate(
        self,
        pdf_in: Path,
        pdf_out: Path,
        validation_result: ValidationResult,
    ) -> RemediationAction:
        """Run the fix. Must be idempotent and deterministic.

        Args:
            pdf_in: Source PDF (read-only; never mutate).
            pdf_out: Target path for the remediated PDF.
            validation_result: The exact error node from the Inspector JSON.

        Returns:
            RemediationAction with success=True only if the fix was applied
            without quality loss. Quality loss must set success=False and populate
            quality_loss_warnings with actionable technical detail.
        """

    def _ok(
        self,
        codigo: str,
        changes: list[str],
        log: str,
    ) -> RemediationAction:
        return RemediationAction(
            codigo=codigo,
            remediator=self.name,
            success=True,
            changes_applied=changes,
            technical_log=log,
        )

    def _fail(
        self,
        codigo: str,
        warnings: list[str],
        log: str,
    ) -> RemediationAction:
        return RemediationAction(
            codigo=codigo,
            remediator=self.name,
            success=False,
            quality_loss_warnings=warnings,
            technical_log=log,
        )
