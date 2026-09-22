# Current Task

## Now

Deployment of Izzy2 is complete at the API/DB layer. The next phase is Telegram exposure and integration, not a replacement of the current API.

## Done

- Reviewed the repository and published the project/reporting skill.
- Added Alembic initial migration and production startup migration step.
- Kept `EXECUTION_ENABLED=false`; unimplemented execution cannot claim `executed`.
- Added deployment and Telegram cutover documentation.
- VPS `147.45.238.131` was backed up and switched from the old `AI-ssistant` stack to Izzy2.
- Izzy2 is deployed at `/root/projects/Izzy2/release` on `127.0.0.1:8000`.
- API and PostgreSQL are healthy; live/readiness and auth smoke checks passed.
- Old app containers are stopped; old volume and backup remain for rollback.

## Next

- Decide whether Telegram should be receive-only first or receive/reply with approval UI.
- Obtain a domain pointing to `147.45.238.131`.
- Install/configure HTTPS reverse proxy.
- Implement Telegram send/reply and approval callback flow before setting the bot webhook.
- Add integration tests and revisit concurrent proposal transitions.

## Blockers

- No public HTTPS endpoint or reverse proxy on the VPS.
- Izzy2 currently accepts Telegram webhook payloads locally but does not send Telegram replies or render approval buttons.
- New database is intentionally empty; old application data was not migrated.
- Local test environment lacks installed Python dependencies; VPS container build and runtime smoke checks passed.
