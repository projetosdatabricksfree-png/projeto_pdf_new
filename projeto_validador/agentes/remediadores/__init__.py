"""Gold layer: deterministic PDF remediators.

Sprint A additions:
  BleedRemediator        — G002: mirror-edge bleed generation
  SafetyMarginRemediator — E004: shrink-to-safe 97% content scaling

Contract (post-Sprint A): success=True whenever the operation completed;
quality degradations go in quality_loss_warnings, never block delivery.
"""
