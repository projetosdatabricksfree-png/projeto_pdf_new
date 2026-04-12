#!/bin/bash
# test_backend.sh: End-to-end terminal validation

echo "--- [1] Checking sample file ---"
if [ ! -f "sample.pdf" ]; then
    echo "Downloading sample PDF..."
    curl -o sample.pdf https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
fi

echo "--- [2] Uploading via CURL to API ---"
RESPONSE=$(curl -s -X POST -F "file=@sample.pdf" http://localhost:8000/api/v1/validate)
JOB_ID=$(echo $RESPONSE | grep -oP '(?<="job_id":")[^"]+')

if [ -z "$JOB_ID" ]; then
    echo "ERROR: Could not get Job ID. Response: $RESPONSE"
    exit 1
fi

echo "Job created: $JOB_ID"
echo "--- [3] Monitoring Workers ---"
echo "Waiting for logs... (Press Ctrl+C to stop manual tail)"

# We will monitor till status is DONE or FAILED in DB
timeout 120s docker compose logs -f worker &
LOG_PID=$!

while true; do
  STATUS_RESP=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/status)
  STATUS=$(echo $STATUS_RESP | grep -oP '(?<="status":")[^"]+')
  PROGRESS=$(echo $STATUS_RESP | grep -oP '(?<="progress":)[^,]+')
  
  echo "Current Status: $STATUS ($PROGRESS%)"
  
  if [ "$STATUS" == "COMPLETED" ] || [ "$STATUS" == "FAILED" ] || [ "$STATUS" == "REPROVADO" ] || [ "$STATUS" == "APROVADO" ]; then
    echo "--- FINAL RESULT REACHED: $STATUS ---"
    kill $LOG_PID
    break
  fi
  sleep 5
done

echo "--- [4] Database Verification ---"
docker exec projeto_validador-api-1 python3 -c "import sqlite3; conn = sqlite3.connect('/app/data/validador.db'); c = conn.cursor(); c.execute('SELECT status, processing_agent FROM jobs WHERE id=\"$JOB_ID\"'); print(f'DB RESULT: {c.fetchone()}')"
