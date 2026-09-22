# Подготовка к развертыванию Izzy2

Дата проверки: 2026-09-22

Коммит: `e484d92`

## Итог

Проект можно развернуть как ограниченный backend-скелет через Docker Compose. Для production-сервера он пока **не готов к закрытию deployment**: не реализованы миграции, reverse proxy/TLS, CI, worker/outbox и реальные Gmail/Calendar/Telegram-интеграции.

Текущий безопасный режим — `EXECUTION_ENABLED=false`. Включать его нельзя: при включении код помечает proposal как `executed`, хотя реальные внешние адаптеры ещё отсутствуют.

## Что требуется на сервере

### Обязательная инфраструктура

- Linux VPS с Docker Engine и Docker Compose v2.
- DNS-имя, направленное на сервер, если API будет доступен извне.
- Nginx или Caddy перед API для TLS, ограничения доступа и, при необходимости, rate limit.
- Firewall: наружу открыть только SSH и HTTPS; PostgreSQL оставить во внутренней Docker-сети.
- Диск с отдельным контролем свободного места для PostgreSQL и backup-файлов.
- Часовая синхронизация и настроенный UTC на сервере.

### Секреты и конфигурация

В `/opt/izzy2/.env` нужно создать значения, не коммитить их в Git и не выводить в логи:

- `POSTGRES_PASSWORD` — пароль PostgreSQL;
- `DATABASE_URL` — URL с теми же именами БД/пользователя/пароля;
- `API_TOKEN` — случайная строка минимум 32 символа;
- `APPROVAL_SIGNING_KEY` — отдельный случайный ключ минимум 32 символа;
- `TELEGRAM_WEBHOOK_SECRET` — отдельный секрет минимум 32 символа;
- `TELEGRAM_OWNER_USER_ID` — Telegram ID владельца;
- `APP_ENV=production`;
- `EXECUTION_ENABLED=false` до отдельного review адаптеров.

Нужно также проверить, что `APP_PORT` не конфликтует с другими сервисами и что `APP_TIMEZONE` соответствует принятой пользовательской зоне. Все секреты должны быть сгенерированы независимо, а не скопированы из `.env.example`.

## Текущий запуск

Предполагаемый порядок для тестового стенда:

```bash
git clone git@github.com:AABrovarnik/Izzy2.git /opt/izzy2
cd /opt/izzy2
cp .env.example .env
# заменить все replace-/change-me значения
docker compose config
docker compose up -d --build
curl -fsS http://127.0.0.1:8000/health/live
curl -fsS http://127.0.0.1:8000/health/ready
```

В текущей версии `init_db()` вызывает `Base.metadata.create_all()`. Это подходит для первого стенда, но не является production-миграцией.

## Что нужно сделать до production

1. Добавить Alembic и начальную миграцию; убрать зависимость production от `create_all()`.
2. Исправить конкурентные переходы proposal через row lock или атомарный `UPDATE ... WHERE status/version`; добавить concurrency tests.
3. Не переводить proposal в `executed` без подтверждённого внешнего адаптера; реализовать transactional outbox и worker.
4. Добавить реальный контракт Telegram delivery/callback и отдельную аутентификацию callback.
5. Добавить CI: установка зависимостей, pytest, lint/type checks, `docker compose config`.
6. Добавить Nginx/Caddy, TLS, security headers, rate limit и ограничение административного API.
7. Настроить backup PostgreSQL, retention, шифрование/защиту backup-файлов и обязательную проверку restore.
8. Добавить мониторинг health/readiness, диска, PostgreSQL, рестартов контейнеров и ошибок интеграций.
9. Ввести redaction/retention policy для Telegram content, proposal payload и audit trail.
10. Провести отдельный security review перед включением Gmail/Calendar write scopes.

## Проверки в текущем окружении

Подтверждено:

- Docker: `29.1.3`;
- Docker Compose: `2.40.3`;
- Python: `3.12.3`;
- `python -m compileall -q app tests` — успешно;
- `sh -n scripts/backup.sh` — успешно;
- рабочая ветка чистая и синхронизирована с `origin/main`.

Не подтверждено:

- фактический запуск контейнеров на целевом сервере;
- доступность и состояние PostgreSQL;
- TLS/DNS/firewall;
- миграции и restore backup;
- pytest: в текущем окружении команда `pytest` отсутствует;
- Telegram/Gmail/Calendar/OpenClaw — адаптеры ещё не реализованы.

## Критерии готовности

Развертывание можно считать закрытым только после того, как на целевом сервере независимо подтверждены:

- `docker compose config` без предупреждений о секретах и missing variables;
- контейнеры `api` и `postgres` в состоянии healthy;
- live/readiness endpoints отвечают через локальный и TLS-маршрут;
- API отклоняет запросы без Bearer token;
- PostgreSQL не слушает публичный интерфейс;
- backup создан и восстановлен в отдельную тестовую БД;
- миграции применяются повторно без разрушения данных;
- после перезапуска сервис возвращается в ready-состояние;
- `EXECUTION_ENABLED=false` подтверждено в effective runtime configuration;
- rollback и контакт ответственного оператора документированы.

## Статус по слоям

- Source: частично готов — Compose и контейнер есть, production-критичные компоненты отсутствуют.
- Tests: частично проверено — статические проверки успешны, pytest и integration tests не выполнены.
- Runtime: не проверен на целевом сервере.
- Production: не закрыт.
