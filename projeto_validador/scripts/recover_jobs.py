import sqlite3
import json
from datetime import datetime, timezone
from celery import Celery
import os

# Celery config
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
app = Celery("preflight_validator", broker=CELERY_BROKER_URL)

def recover_jobs():
    conn = sqlite3.connect('/app/data/validador.db')
    cursor = conn.cursor()
    
    # Get jobs that are stuck (not DONE/FAILED)
    cursor.execute("SELECT id, original_filename, file_path, file_size_bytes, client_locale, submitted_at FROM jobs WHERE status NOT IN ('DONE', 'FAILED')")
    jobs = cursor.fetchall()
    
    print(f"Found {len(jobs)} stuck jobs. Re-queueing...")
    
    for job in jobs:
        job_id, original_filename, file_path, file_size_bytes, client_locale, submitted_at = job
        
        # Build payload matching JobPayload schema
        job_payload = {
            "job_id": job_id,
            "file_path": file_path,
            "original_filename": original_filename,
            "file_size_bytes": file_size_bytes,
            "submitted_at": submitted_at,
            "client_locale": client_locale
        }
        
        # Metadata (defaulting to none as we don't store it separate in Job table, 
        # but task_route handles default values)
        job_metadata = {
            "gramatura_gsm": 0,
            "encadernacao": "none",
            "grain_direction": "unknown"
        }
        
        print(f"Re-queueing job {job_id} ({original_filename})")
        
        # Send to queue:jobs where task_route is listening
        app.send_task(
            "workers.tasks.task_route",
            args=[json.dumps(job_payload), json.dumps(job_metadata)],
            queue="queue:jobs"
        )
        
        # Reset status to QUEUED in DB to match
        cursor.execute("UPDATE jobs SET status='QUEUED' WHERE id=?", (job_id,))
        
    conn.commit()
    conn.close()
    print("Recovery complete.")

if __name__ == "__main__":
    recover_jobs()
