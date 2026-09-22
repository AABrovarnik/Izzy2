# Deployment preparation plan

## Objective

Prepare Izzy2 for a controlled VPS deployment and document how the existing Telegram bot can be cut over to the new webhook without exposing bot credentials or enabling external actions prematurely.

## Assumptions

- The target server has Docker Engine/Compose v2 and a public DNS name.
- The existing Telegram bot token is available to the operator but will not be committed or pasted into the repository.
- The first deployment remains receive-only: `EXECUTION_ENABLED=false`.
- Gmail/Calendar/OpenClaw adapters are out of scope for this phase.

## Steps

1. [done] Add reproducible database migrations and make startup behavior explicit for production.
2. [done] Add deployment configuration and operator documentation, including Telegram webhook cutover and rollback.
3. [done] Harden the proposal execution guard so enabling the flag cannot claim execution without an adapter.
4. [partial] Add or extend tests for migration/startup configuration and the safe Telegram/deployment path.
5. [in progress] Run source checks and prepare a commit for publication. Do not perform VPS deployment or Telegram `setWebhook` without explicit server/bot access.

## Acceptance criteria

- A fresh deployment can apply a versioned schema before starting the API.
- Existing data has a documented migration/backup path.
- Telegram cutover instructions use a secret placeholder and include verification/rollback.
- `EXECUTION_ENABLED=true` cannot mark an unimplemented action as executed.
- Checks and their limitations are recorded in `doc/`.

## Rollback

- Revert the deployment commit and restore the previous container image.
- Before schema changes, take a PostgreSQL custom-format backup and verify the file exists.
- Roll back Telegram by restoring the old webhook URL with the old secret; do not delete the bot or rotate tokens as part of this phase.
