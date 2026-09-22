# Оценка AI-secretary-v1.0 и изменения в v2

## Итоговая оценка

Исходный архив хорошо задаёт направление, но **не является разворачиваемым приложением**. Это архитектурно-техническое ТЗ: в архиве 10 файлов и около 14 KB текста, отсутствуют исходники, `Dockerfile`, зависимости, миграции, тесты и рабочие адаптеры Telegram/Gmail/Calendar/OpenClaw.

## Что сделано хорошо

### 1. Правильно выбран режим Human-in-the-loop

Исходник запрещает автоматические отправки, изменения календаря, архивацию и массовые операции без approval. Это сильное продуктовое ограничение для секретаря: цена ошибочного внешнего действия выше цены лишнего вопроса.

**В v2:** сохранены отдельные статусы proposal, TTL, версия и явные `approve/reject/snooze/execute`. Внешнее исполнение по умолчанию отключено.

### 2. Хорошо описана защита approval

Есть одноразовый approval, TTL, проверка владельца, версии и idempotency key; отдельно отмечена защита от replay.

**В v2:** реализован HMAC-токен, nonce хранится только как SHA-256 hash, plaintext-токен не записывается в БД, повторное действие после смены статуса даёт 409, просроченное — 410.

### 3. Верно выделены временные зоны и часовые пояса

Исходник требует UTC в БД, timezone в пользовательском интерфейсе и отдельно предупреждает про all-day события и recurrence.

**В v2:** datetime-поля timezone-aware в API-моделях, timezone хранится у task. На следующем слое адаптеров нельзя преобразовывать all-day даты в полночь без отдельной семантики.

### 4. Хорошая базовая модель эксплуатационной безопасности

Отмечены allowlist Telegram, закрытые PostgreSQL/Redis, health/readiness, backup/restore, PII-redacted logs, retry/DLQ и non-public OpenClaw.

**В v2:** Telegram secret header, Bearer API auth, health endpoints, non-root container, PostgreSQL без внешнего порта и backup script. PII-redaction и полноценные outbox/DLQ пока оставлены как обязательные следующие этапы, а не объявлены готовыми.

### 5. Полезная поэтапная реализация

План начинается с основы и read-only режима, а write-действия и отправка откладываются. Такой порядок снижает риск слишком ранней автоматизации.

**В v2:** первый слой действительно можно запустить; Gmail/Calendar/OpenClaw не подменяются mock-успехом.

## Что требовало доработки

### 1. Это был план, а не поставляемый продукт

В README описан `docker compose up`, но в архиве нет Dockerfile и каталога приложения. Нельзя выполнить API, worker, миграции или тесты.

**Исправлено:** добавлены `Dockerfile`, `requirements.txt`, `app/`, Compose, тесты и инструкции запуска.

### 2. Не был определён контракт выдачи approval token

В API описан `approval_token`, но не объяснено, где создаётся токен, как он доставляется в Telegram и как он хранится. Простое хранение токена в БД создало бы лишний риск.

**Исправлено:** v2 создаёт nonce, хранит только его hash и подписывает `proposal_id:version:nonce`. Важное ограничение зафиксировано явно: транспорт доставки карточки ещё должен использовать этот токен, а DB его не сохраняет.

### 3. Не было конкретной транзакционной реализации дедупликации

Указаны unique constraints и idempotency, но не показана атомарная обработка гонок, повторных webhook и повторного execute.

**Исправлено частично:** есть уникальный idempotency key, уникальная пара Telegram source type/external_id и идемпотентный возврат ранее принятого webhook. Для настоящего распределённого worker ещё нужен transactional outbox и DB-level locking; это явно отмечено.

### 4. Compose ссылался на компоненты без реализации

Исходный Compose запускал API, worker, Redis и OpenClaw, хотя их код, health contracts, очереди и конфигурация отсутствовали. Это создаёт ложное ощущение готовности.

**Исправлено:** v2 запускает только реализованные API и PostgreSQL. Redis, OpenClaw и worker появятся вместе с кодом их контрактов, а не как декоративные контейнеры.

### 5. Секреты и конфигурация были обозначены, но не валидировались

`.env.example` содержал `replace-me`, однако production мог бы стартовать с небезопасными значениями.

**Исправлено:** production-конфигурация требует API token, signing key и Telegram secret длиной не менее 32 символов. Значения не логируются и не попадают в модель данных.

### 6. OAuth и внешние записи были обещаны, но не ограничены технически

Документ правильно рекомендовал read-only scopes, но не было кода, который реально блокирует отправку писем или создание событий до approval и scope review.

**Исправлено:** v2 не делает внешних вызовов вообще и возвращает 501 при `EXECUTION_ENABLED=false`. Это безопаснее, чем имитация Gmail/Calendar. Реальные адаптеры должны быть добавлены с отдельными scopes и тестами.

### 7. Не было минимальных проверок качества

В исходнике есть требование покрытия критической логики и список E2E сценариев, но нет тестового набора.

**Исправлено частично:** добавлены smoke-тесты подписи approval token и timezone-aware времени. Перед production остаются интеграционные тесты API, Postgres, Telegram replay, concurrent approve/execute, migrations и provider fakes.

## Что сознательно не заявляется готовым

- OAuth Google и шифрование refresh tokens;
- реальная синхронизация Gmail History API/polling;
- Calendar free/busy и проверка access role;
- Telegram bot delivery/edit cards;
- OpenClaw/LLM routing, JSON schema validation и prompt-injection guard;
- transactional outbox, Redis locks, worker, retry/DLQ;
- Nginx/Caddy TLS-конфигурация, мониторинг и restore test.

Это не пропуски в документации: для них нужны отдельные provider contracts, секреты и эксплуатационные решения. Без них было бы неправильно называть пакет production-ready.

## Рекомендуемый порядок следующей реализации

1. Alembic migrations и transactional outbox.
2. Telegram adapter: доставка карточки с токеном, callback allowlist, replay tests.
3. LLM analyzer с Pydantic schema, redaction и 30–50 adversarial cases.
4. Gmail/Calendar read-only adapters и fake provider tests.
5. Calendar CREATE_EVENT adapter с идемпотентным external key и conflict check.
6. Worker, Redis lock, retry/DLQ, reminders и digest.
7. TLS, backups, restore rehearsal, metrics и security review.