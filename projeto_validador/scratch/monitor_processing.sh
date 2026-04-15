#!/bin/bash
DURATION=$((5 * 60))
INTERVAL=15
END_TIME=$(($(date +%s) + DURATION))

echo "Monitoring started at $(date)"
echo "-----------------------------------"

while [ $(date +%s) -lt $END_TIME ]; do
    echo "Time: $(date)"
    echo "--- Queue Status ---"
    # Try common celery queue names
    echo -n "Celery Queue Length: "
    docker compose -f /home/diego/Desktop/PROJETOS/Projeto_grafica/projeto_validador/docker-compose.yml exec redis redis-cli LLEN celery 2>/dev/null || echo "N/A"
    
    echo "--- Worker Logs (last 5 lines) ---"
    docker compose -f /home/diego/Desktop/PROJETOS/Projeto_grafica/projeto_validador/docker-compose.yml logs --tail=5 worker
    
    echo "--- Resource Usage ---"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" projeto_validador-worker-1 projeto_validador-api-1
    
    echo "-----------------------------------"
    sleep $INTERVAL
done

echo "Monitoring completed at $(date)"
