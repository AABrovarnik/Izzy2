#!/usr/bin/env sh
set -eu

: "${BACKUP_DIR:=./backups}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"

mkdir -p "$BACKUP_DIR"
file="$BACKUP_DIR/${POSTGRES_DB}-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose exec -T postgres pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB" > "$file"
echo "Created $file"
