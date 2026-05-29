# Payments Processing Service

Асинхронный сервис процессинга платежей на FastAPI, PostgreSQL, SQLAlchemy 2.0 async, RabbitMQ/FastStream и Alembic.

## Запуск

Заполните `.env` по примеру `.env.example`, затем запустите:

```bash
docker compose up --build
```

API будет доступен на `http://localhost:8000`, Swagger на `http://localhost:8000/swagger/`.

RabbitMQ Management UI: `http://localhost:15672`. Логин и пароль берутся из `RABBITMQ_USER` и `RABBITMQ_PASSWORD`.

## Создание платежа

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: order-1001" \
  -d '{
    "amount": "1500.00",
    "currency": "RUB",
    "description": "Test payment",
    "metadata": {"order_id": "1001"},
    "webhook_url": "https://webhook.site/your-url"
  }'
```

Ответ: `202 Accepted` с `payment_id`, `status`, `created_at`.

## Получение платежа

```bash
curl http://localhost:8000/api/v1/payments/<payment_id> \
  -H "X-API-Key: $API_KEY"
```

## Архитектура

1. API в одной транзакции создает запись в `payments`, запись в `idempotency_keys` и событие в `outbox`.
2. `outbox-worker` читает неопубликованные события через `FOR UPDATE SKIP LOCKED`, публикует persistent message в `payments.events` и только после успешной публикации помечает событие опубликованным.
3. `consumer` читает `payments.new`, эмулирует обработку 2-5 секунд, обновляет статус платежа и отправляет webhook.
4. Ошибки обработки/webhook уходят в retry-очереди `payments.new.retry.2/3` с TTL 1/2 секунды. Всего выполняется 3 delivery-попытки, после чего сообщение попадает в `payments.new.dlq`.

## RabbitMQ topology

- `payments.events`: durable topic exchange для бизнес-событий.
- `payments.new`: durable quorum queue, binding key `payments.new`.
- `payments.new.retry.2/3`: durable quorum TTL queues.
- `payments.new.dlq`: durable quorum DLQ.

Гарантия доставки outbox здесь at-least-once: событие не теряется между БД и RabbitMQ. Дубликаты возможны при сбое между publish и отметкой `published=true`, поэтому consumer написан идемпотентно по текущему статусу платежа.
