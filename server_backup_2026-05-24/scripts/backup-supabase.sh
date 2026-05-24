#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d-%H%M%S)"
STACK_DIR="/opt/stack/supabase"
BACKUP_DIR="/opt/stack/backups/supabase"
mkdir -p "$BACKUP_DIR"
cd "$STACK_DIR"

if ! docker compose --env-file .env -f docker-compose.yml ps db | grep -q 'running\|Up'; then
  echo "supabase backup failed: db is not running" >&2
  exit 1
fi

docker compose --env-file .env -f docker-compose.yml exec -T db pg_dumpall -U postgres | gzip > "$BACKUP_DIR/supabase-db-$TS.sql.gz"
sha256sum "$BACKUP_DIR/supabase-db-$TS.sql.gz" > "$BACKUP_DIR/supabase-$TS.sha256"
find "$BACKUP_DIR" -type f -mtime +14 -delete
echo "supabase backup ok: $TS"
