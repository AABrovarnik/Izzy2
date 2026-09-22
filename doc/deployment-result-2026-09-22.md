# Результат развертывания Izzy2

Дата: 2026-09-22

## Выполнено

- Старые контейнеры `ai-secretary-api`, `ai-secretary-worker`, `ai-secretary-db` остановлены и удалены.
- Старый Docker volume оставлен для rollback.
- Backup старой PostgreSQL базы создан до переключения:
  `/root/projects/AI-ssistant/backups/pre-izzy2-20260922T203731Z.dump`
- `Izzy2` развернут из commit `a9153ea` в `/root/projects/Izzy2/release`.
- Новый API слушает `127.0.0.1:8000`.
- Новая PostgreSQL база изолирована в отдельном Docker volume.
- `EXECUTION_ENABLED=false`.

## Проверенные runtime-критерии

- `release-api-1`: healthy.
- `release-postgres-1`: healthy.
- `GET /health/live`: `200`, `{"status":"ok"}`.
- `GET /health/ready`: `200`, база доступна.
- API без Bearer token: `401`.
- API с Bearer token: `GET /api/v1/tasks` возвращает `200` и пустой список.
- Alembic version: `0001_initial_schema`.
- `.env` имеет права `600`.
- Старые контейнеры отсутствуют.

## Ограничения после замены

- Новая база пустая; данные старого приложения не переносились.
- Nginx/Caddy и HTTPS на сервере отсутствуют.
- Telegram webhook не установлен.
- Старый polling worker остановлен; текущий Izzy2 принимает webhook только локально и не отправляет ответы/approval-кнопки.
- Поэтому API развернут и проверен, но Telegram-интеграция production не закрыта.

## Rollback

1. Остановить стек `/root/projects/Izzy2/release`.
2. Восстановить старый compose-проект из `/root/projects/AI-ssistant`.
3. Использовать сохраненный volume и backup при необходимости.

Rollback не выполнялся.
