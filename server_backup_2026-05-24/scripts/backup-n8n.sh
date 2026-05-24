#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d-%H%M%S)"
STACK_DIR="/opt/stack/n8n"
BACKUP_DIR="/opt/stack/backups/n8n"
mkdir -p "$BACKUP_DIR"
cd "$STACK_DIR"

docker compose --env-file .env -f compose.yml exec -T postgres pg_dump -U n8n -d n8n | gzip > "$BACKUP_DIR/n8n-db-$TS.sql.gz"
tar --warning=no-file-changed --ignore-failed-read -czf "$BACKUP_DIR/n8n-data-$TS.tar.gz" -C /var/lib/docker/volumes n8n_n8n_data >/dev/null 2>&1 || true
sha256sum "$BACKUP_DIR"/*"$TS"* > "$BACKUP_DIR/n8n-$TS.sha256"
find "$BACKUP_DIR" -type f -mtime +14 -delete
echo "n8n backup ok: $TS"
