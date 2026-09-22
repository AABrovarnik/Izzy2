# Переключение существующего Telegram-бота на Izzy2

Этот документ описывает безопасный cutover. Токен бота не хранится в Git и не вставляется в `.env` репозитория в открытом виде.

## Перед переключением

- Развернуть API за HTTPS, например `https://assistant.example.com`.
- Проверить `GET /health/live` и `GET /health/ready` локально и через reverse proxy.
- Установить в `.env` новый `TELEGRAM_WEBHOOK_SECRET` и `TELEGRAM_OWNER_USER_ID`.
- Оставить `EXECUTION_ENABLED=false`.
- Сохранить текущий webhook старого приложения и сделать backup базы.

## Проверка текущего webhook

На машине, где хранится bot token:

```bash
export TELEGRAM_BOT_TOKEN='не_хранить_в_репозитории'
curl -fsS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

Зафиксировать `url`, `pending_update_count` и `last_error_message` до переключения.

## Установка нового webhook

```bash
export TELEGRAM_WEBHOOK_SECRET='значение_из_.env'
curl -fsS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  --data-urlencode 'url=https://assistant.example.com/api/v1/webhooks/telegram' \
  --data-urlencode "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
  --data-urlencode 'drop_pending_updates=false'
```

После ответа `ok: true` повторно вызвать `getWebhookInfo` и отправить одно тестовое сообщение от разрешённого Telegram user. Проверить запись в `sources` и отсутствие 401/403/5xx в логах.

## Откат

Если новый endpoint не принимает обновления, немедленно вернуть URL старого приложения:

```bash
curl -fsS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  --data-urlencode 'url=https://old.example.com/<old-webhook-path>' \
  --data-urlencode 'secret_token=<old-secret>' \
  --data-urlencode 'drop_pending_updates=false'
```

Старый URL и secret нужно подставлять только из сохраненной конфигурации старого приложения. Не вращать bot token в рамках этой операции.

## Ограничение текущей версии

Izzy2 сейчас принимает Telegram updates и сохраняет `Source`, но не реализует отправку сообщений обратно в Telegram и callback-кнопки approval. Поэтому переориентация бота на этот endpoint является только receive-only этапом; полноценный conversational bot и approval UI требуют отдельной реализации.
