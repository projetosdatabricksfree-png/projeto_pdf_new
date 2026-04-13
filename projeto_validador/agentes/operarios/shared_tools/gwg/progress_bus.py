"""
Progress Bus — publishes per-checker progress to Redis so the frontend can
render a deterministic "Etapa N de M" board instead of a vague percentage.

Keyspace: job:{job_id}:progress  (string, JSON)
TTL: 1h (auto-expire — progress is ephemeral)
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_PROGRESS_TTL_S = 3600
_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import redis
        _client = redis.Redis.from_url(_REDIS_URL, decode_responses=True, socket_timeout=2)
        _client.ping()
    except Exception as exc:
        logger.warning(f"[progress_bus] Redis indisponível: {exc!r}")
        _client = False
    return _client


def _key(job_id: str) -> str:
    return f"job:{job_id}:progress"


def init_progress(job_id: str, stages: list[dict]) -> None:
    """Initialize the progress board for a job with the full stage list.

    stages: [{"name": "geometry", "label": "Geometria"}, ...]
    """
    if not job_id:
        return
    client = _get_client()
    if not client:
        return
    payload = {
        "job_id": job_id,
        "total": len(stages),
        "done": 0,
        "started_at": time.time(),
        "current": None,
        "stages": [
            {"name": s["name"], "label": s["label"], "status": "PENDING", "duration_ms": 0}
            for s in stages
        ],
    }
    try:
        client.set(_key(job_id), json.dumps(payload), ex=_PROGRESS_TTL_S)
    except Exception as exc:
        logger.warning(f"[progress_bus] init falhou: {exc!r}")


def update_stage(job_id: str, name: str, status: str, duration_ms: int | None = None) -> None:
    """Update one stage (RUNNING / OK / ERRO / AVISO / TIMEOUT)."""
    if not job_id:
        return
    client = _get_client()
    if not client:
        return
    try:
        raw = client.get(_key(job_id))
        if not raw:
            return
        data = json.loads(raw)
        for stage in data["stages"]:
            if stage["name"] == name:
                stage["status"] = status
                if duration_ms is not None:
                    stage["duration_ms"] = duration_ms
                break
        if status == "RUNNING":
            data["current"] = name
        elif status in ("OK", "ERRO", "AVISO", "TIMEOUT", "FAILED"):
            data["done"] = sum(1 for s in data["stages"] if s["status"] not in ("PENDING", "RUNNING"))
            if data["current"] == name:
                data["current"] = None
        client.set(_key(job_id), json.dumps(data), ex=_PROGRESS_TTL_S)
    except Exception as exc:
        logger.warning(f"[progress_bus] update falhou: {exc!r}")


def get_progress(job_id: str) -> dict[str, Any] | None:
    """Read progress for a job (used by the FastAPI endpoint)."""
    if not job_id:
        return None
    client = _get_client()
    if not client:
        return None
    try:
        raw = client.get(_key(job_id))
        return json.loads(raw) if raw else None
    except Exception:
        return None
