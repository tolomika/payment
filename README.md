# Payments Service

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
    "webhook_url": "http://localhost:8000/payment/webhook"
  }'
```

## Получение платежа

```bash
curl http://localhost:8000/api/v1/payments/<payment_id> \
  -H "X-API-Key: $API_KEY"
```

## RabbitMQ topology

- `payments.events`: durable topic exchange для бизнес-событий.
- `payments.new`: durable quorum queue, binding key `payments.new`.
- `payments.new.retry.2/3`: durable quorum TTL queues.
- `payments.new.dlq`: durable quorum DLQ.

Гарантия доставки outbox здесь at-least-once: событие не теряется между БД и RabbitMQ. Дубликаты возможны при сбое между publish и отметкой `published=true`, поэтому consumer написан идемпотентно по текущему статусу платежа.
