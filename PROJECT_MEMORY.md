# Project Memory

## Repository and deployment

- Repository: `AABrovarnik/Izzy2`.
- Deployment commit: `a9153ea`.
- Deployment result documentation commit: `276f612`.
- VPS: `147.45.238.131`; project path: `/root/projects/Izzy2/release`.
- Current service: `release-api-1` and `release-postgres-1`, API bound to `127.0.0.1:8000`.
- Production `.env` is server-only with mode `600`; no secrets belong in Git.
- `EXECUTION_ENABLED=false` is intentional until real idempotent adapters exist.

## Safety and rollback

- Old `AI-ssistant` containers were stopped and removed during replacement.
- Old Docker volume was preserved.
- Pre-switch PostgreSQL backup: `/root/projects/AI-ssistant/backups/pre-izzy2-20260922T203731Z.dump`.
- Rollback means stop `/root/projects/Izzy2/release` and restore the old Compose stack/volume or backup.

## Current capability boundary

- Working: FastAPI health endpoints, authenticated task/source/proposal APIs, PostgreSQL, Alembic, approval token flow, Telegram update ingestion, audit records.
- Not implemented: Gmail/Calendar/OpenClaw adapters, worker/outbox, Telegram replies and approval buttons, public HTTPS, external execution.
- The new database is empty; no old application data was migrated.

## Operational evidence

- Runtime checks passed: `/health/live` and `/health/ready` returned `200`; unauthenticated API returned `401`; authenticated task listing returned `200`.
- Alembic version on VPS: `0001_initial_schema`.
- Old application had a Telegram polling conflict (`409`) from two worker processes; old polling stopped with the old stack.
