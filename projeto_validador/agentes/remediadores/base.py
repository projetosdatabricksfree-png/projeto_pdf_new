"""
Base contract for all remediators.

Remediators are deterministic: given a PDF and a specific ValidationResult node,
they produce a new PDF (or fail cleanly) and a RemediationAction describing what
changed. They never use LLMs and never guess.

Contract (post-Sprint A — "Entregar sempre, auditar tudo"):
- success=True  whenever the operation completed, even if quality was degraded.
  Degradations are recorded in quality_loss_warnings for traceability.
- success=False is reserved exclusively for: binary missing, timeout, or
  unrecoverable exception. Never fail on a policy decision.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.api.schemas import RemediationAction, ValidationResult

logger = logging.getLogger(__name__)


class RemediatorError(Exception):
    """Raised when a remediator encounters an unrecoverable technical failure."""


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
            RemediationAction with success=True when the operation completed
            (including cases with quality degradation — those go in
            quality_loss_warnings). success=False only for technical failures.
        """

    def _ok(
        self,
        codigo: str,
        changes: list[str],
        log: str,
    ) -> RemediationAction:
        """Return a clean success with no quality loss."""
        return RemediationAction(
            codigo=codigo,
            remediator=self.name,
            success=True,
            changes_applied=changes,
            technical_log=log,
        )

    def _warn(
        self,
        codigo: str,
        changes: list[str],
        warnings: list[str],
        log: str,
        severity: str = "low",
    ) -> RemediationAction:
        """Return success=True with quality-loss warnings recorded."""
        return RemediationAction(
            codigo=codigo,
            remediator=self.name,
            success=True,
            changes_applied=changes,
            quality_loss_warnings=warnings,
            quality_loss_severity=severity,
            technical_log=log,
        )

    def _fail(
        self,
        codigo: str,
        warnings: list[str],
        log: str,
    ) -> RemediationAction:
        """Return success=False for genuine technical failures only."""
        return RemediationAction(
            codigo=codigo,
            remediator=self.name,
            success=False,
            quality_loss_warnings=warnings,
            technical_log=log,
        )
