# AI Secretary v2

Рабочий безопасный backend-скелет для развёртывания на VPS. Это не «готовая интеграция Gmail/Google Calendar», а минимальная исполняемая основа, в которую такие адаптеры добавляются отдельно.

## Что уже работает

- FastAPI API с `/health/live` и `/health/ready`;
- PostgreSQL 16 в Docker Compose, локальный SQLite для разработки;
- задачи и proposals с версиями, TTL, одноразовым HMAC approval token и idempotency key;
- reject/snooze без внешних побочных эффектов;
- Telegram webhook с секретом и дедупликацией `update_id`;
- append-only audit trail;
- запрет внешнего исполнения по умолчанию (`EXECUTION_ENABLED=false`);
- контейнер с non-root пользователем, приватный bind-порт и healthcheck;
- базовый backup-скрипт и тесты критической криптографической логики.

## Быстрый запуск на VPS

```bash
cp .env.example .env
# замените все replace-me/replace-with значения случайными секретами
docker compose config
docker compose up -d --build
curl http://127.0.0.1:8000/health/ready
```

Перед публикацией через Nginx/Caddy добавьте TLS, firewall и ограничение доступа к API. PostgreSQL наружу не публикуется.

## Approval flow

1. Внутренний анализатор создаёт `POST /api/v1/proposals` с `Idempotency-Key` в JSON.
2. Ответ содержит DTO proposal, а одноразовый токен возвращается авторизованному внутреннему вызывающему в заголовке `X-Approval-Token`. Telegram-адаптер передаёт его в канал доставки карточки; в БД plaintext-токен не хранится.
3. Внешний канал отправляет `POST /approve` с `version` и одноразовым токеном.
4. Proposal становится `approved`; отдельный worker вызывает `/execute`.
5. Реальные внешние адаптеры подключаются только после отдельного review. Пока `EXECUTION_ENABLED=false`, `/execute` возвращает 501.

Для production следующий обязательный слой — transactional outbox/worker, Alembic migrations, OAuth token encryption и реальные Gmail/Calendar adapters. Эти вещи не замаскированы под готовые функции.
