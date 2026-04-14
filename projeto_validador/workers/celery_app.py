"""
Celery application factory with queue configuration.

Queue names match exactly the specification in PROMPT_IMPLEMENTACAO.md.
"""
from __future__ import annotations

import os

from celery import Celery

CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/1"))

print(f"[Celery] Initializing with Broker: {CELERY_BROKER_URL}")

celery_app = Celery(
    "preflight_validator",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["workers.tasks"],
)

# Queue configuration — exact names from the specification
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        # Ingestion & routing
        "workers.tasks.task_route": {"queue": "queue:jobs"},
        # Especialista deep-probe (publishes to queue:routing_decisions on completion)
        "workers.tasks.task_process_especialista": {"queue": "queue:especialista"},
        # Dedicated consumer for Especialista → Operário handoff (Rule 3 — Deadlock Prevention)
        "workers.tasks.task_receive_routing_decision": {"queue": "queue:routing_decisions"},
        # Operário workers
        "workers.tasks.task_process_papelaria": {"queue": "queue:operario_papelaria_plana"},
        "workers.tasks.task_process_editoriais": {"queue": "queue:operario_editoriais"},
        "workers.tasks.task_process_dobraduras": {"queue": "queue:operario_dobraduras"},
        "workers.tasks.task_process_cortes": {"queue": "queue:operario_cortes_especiais"},
        "workers.tasks.task_process_cad": {"queue": "queue:operario_projetos_cad"},
        # Downstream
        "workers.tasks.task_validate": {"queue": "queue:validador"},
        "workers.tasks.task_log": {"queue": "queue:audit"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Time limits — prevent a stuck task from holding the worker forever.
    # Soft limit raises SoftTimeLimitExceeded inside the task (catchable).
    # Hard limit sends SIGKILL and the task is re-queued (task_reject_on_worker_lost).
    task_soft_time_limit=600,   # 10 min — raise SoftTimeLimitExceeded
    task_time_limit=900,         # 15 min — SIGKILL
    # Visibility timeout must be >= task_time_limit so a running task is not
    # re-delivered to another worker while still executing.
    broker_transport_options={"visibility_timeout": 3600},
)
