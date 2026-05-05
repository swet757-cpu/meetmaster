#!/usr/bin/env bash
set -euo pipefail

cd /opt/stack/n8n
before=$(sudo docker exec n8n-postgres psql -U n8n -d n8n -At -c 'SELECT COALESCE(max(id),0) FROM execution_entity;')

curl -fsS --max-time 20 \
  -X POST http://127.0.0.1:5678/webhook/amocrm-fintablo-deal \
  -H 'Content-Type: application/json' \
  --data '{"leads[update][0][status_id]":"1","leads[update][0][id]":"TEST_NO_FINTABLO"}' \
  >/dev/null

sleep 2

sudo docker exec n8n-postgres psql -U n8n -d n8n -At -F '|' -c "SELECT id,status,mode,finished FROM execution_entity WHERE id > ${before} ORDER BY id DESC;"
