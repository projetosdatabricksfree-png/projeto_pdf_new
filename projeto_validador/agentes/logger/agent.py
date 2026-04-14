"""
Agente Logger — Audit and persistence agent.

Captures ALL events from ALL agents and persists them in a structured way.
- Async and fault-tolerant: never blocks the pipeline.
- Buffers events in memory if the DB is unavailable (max 1000 events).
- Monitors SLA violations and triggers alerts.
"""
from __future__ import annotations

import json
import logging
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

# SLA thresholds in milliseconds
SLA_THRESHOLDS: dict[str, int] = {
    "operario_papelaria_plana": 180_000,   # 3 min
    "operario_editoriais": 300_000,         # 5 min
    "operario_dobraduras": 240_000,         # 4 min
    "operario_cortes_especiais": 240_000,   # 4 min
    "operario_projetos_cad": 180_000,       # 3 min
    "total_pipeline": 600_000,              # 10 min
}

# Maximum events to buffer when DB is unavailable
MAX_BUFFER_SIZE: int = 1000


class AgenteLogger:
    """Audit agent that persists all system events."""

    def __init__(self) -> None:
        self._buffer: deque[dict] = deque(maxlen=MAX_BUFFER_SIZE)

    async def registrar_evento(self, event_data: dict[str, Any]) -> None:
        """Register an audit event in the database.

        If the database is unavailable, buffers the event for later retry.

        Args:
            event_data: Dictionary with job_id, agent_name, event_type, etc.
        """
        try:
            from app.database.session import async_session_factory
            from app.database.crud import create_event

            async with async_session_factory() as db:
                await create_event(
                    db,
                    job_id=event_data.get("job_id", "unknown"),
                    agent_name=event_data.get("agent_name", "unknown"),
                    event_type=event_data.get("event_type", "INFO"),
                    event_level=event_data.get("event_level", "INFO"),
                    payload=json.dumps(event_data.get("payload", {}), default=str),
                    duration_ms=event_data.get("duration_ms"),
                )
                await db.commit()

            # Flush buffer if we have pending events
            await self._flush_buffer()

        except Exception as exc:
            logger.warning(f"[Logger] DB write failed, buffering event: {exc}")
            self._buffer.append(event_data)

    async def _flush_buffer(self) -> None:
        """Attempt to flush buffered events to the database."""
        if not self._buffer:
            return

        from app.database.session import async_session_factory
        from app.database.crud import create_event

        try:
            async with async_session_factory() as db:
                while self._buffer:
                    event_data = self._buffer.popleft()
                    await create_event(
                        db,
                        job_id=event_data.get("job_id", "unknown"),
                        agent_name=event_data.get("agent_name", "unknown"),
                        event_type=event_data.get("event_type", "INFO"),
                        event_level=event_data.get("event_level", "INFO"),
                        payload=json.dumps(
                            event_data.get("payload", {}), default=str
                        ),
                        duration_ms=event_data.get("duration_ms"),
                    )
                await db.commit()
                logger.info("[Logger] Flushed buffered events successfully")
        except Exception as exc:
            logger.warning(f"[Logger] Buffer flush failed: {exc}")

    async def verificar_sla(
        self,
        job_id: str,
        agent: str,
        duration_ms: int,
    ) -> None:
        """Check if an agent exceeded its SLA threshold and log a violation.

        Args:
            job_id: The job identifier.
            agent: The agent name.
            duration_ms: Duration of the processing in milliseconds.
        """
        threshold = SLA_THRESHOLDS.get(agent, 600_000)

        if duration_ms > threshold:
            await self.registrar_evento({
                "job_id": job_id,
                "agent_name": "logger",
                "event_type": "SLA_VIOLATION",
                "event_level": "WARNING",
                "payload": {
                    "agent": agent,
                    "duration_ms": duration_ms,
                    "threshold_ms": threshold,
                    "overage_ms": duration_ms - threshold,
                },
                "duration_ms": duration_ms,
            })

    async def registrar_routing(
        self,
        job_id: str,
        agent_origin: str,
        route_to: str,
        confidence: float,
        reason: str,
        metadata_snapshot: dict,
    ) -> None:
        """Register a routing decision in the database.

        Args:
            job_id: The job identifier.
            agent_origin: The agent that made the routing decision.
            route_to: The target operário.
            confidence: Confidence score of the routing.
            reason: Reason for the routing decision.
            metadata_snapshot: Metadata used for the decision.
        """
        try:
            from app.database.session import async_session_factory
            from app.database.crud import create_routing_log

            async with async_session_factory() as db:
                await create_routing_log(
                    db,
                    job_id=job_id,
                    agent_origin=agent_origin,
                    route_to=route_to,
                    confidence=confidence,
                    reason=reason,
                    metadata_snapshot=metadata_snapshot,
                )
                await db.commit()
        except Exception as exc:
            logger.warning(f"[Logger] Failed to log routing: {exc}")
