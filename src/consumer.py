import asyncio
import logging
import random
from typing import Any

import httpx
from faststream import AckPolicy
from faststream.rabbit import RabbitMessage


from core.database import db_conn

from schema.payment import PaymentStatus
from service.payment.service import PaymentService
from service.broker.rabbit_connection import (
    app,
    broker,
    declare_topology,
    payments_exchange,
    payments_dlq,
    payments_queue,
    payments_retry_queues,
)

log = logging.getLogger(__name__)



async def send_webhook(url: str, payload: dict[str, Any]) -> None:
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.post(url, json=payload)

        if 200 <= resp.status_code < 300:
            return

        raise Exception(f"Webhook failed: {resp.status_code}")


async def retry_or_dlq(message: dict[str, Any], msg: RabbitMessage) -> None:
    headers = msg.headers or {}
    attempt = int(headers.get("x-delivery-attempt", 1))
    if attempt >= 3:
        await broker.publish(
            message=message,
            queue=payments_dlq,
            routing_key=payments_dlq.routing_key,
            headers={**headers, "x-final-error": "payment processing failed", "x-delivery-attempt": attempt},
            persist=True,
        )
        await msg.ack()
        return

    next_attempt = attempt + 1
    retry_queue = payments_retry_queues[next_attempt - 2]
    await broker.publish(
        message=message,
        queue=retry_queue,
        routing_key=retry_queue.routing_key,
        headers={**headers, "x-delivery-attempt": next_attempt},
        persist=True,
    )
    await msg.ack()


@app.after_startup
async def after_startup() -> None:
    await declare_topology()


@broker.subscriber(payments_queue, payments_exchange, ack_policy=AckPolicy.MANUAL)
async def process_payment(message: dict[str, Any], msg: RabbitMessage) -> None:
    payment_id = message["id"]
    try:
        async with db_conn.session() as session:
            payment_service = PaymentService(session)
            payment = await payment_service.get_payment(payment_id)
            if not payment:
                raise ValueError(f"Payment {payment_id} not found")

            if payment["status"] == PaymentStatus.pending.value:
                await asyncio.sleep(random.uniform(2, 5))
                status = (
                    PaymentStatus.succeeded.value
                    if random.random() > 0.1
                    else PaymentStatus.failed.value
                )
                await payment_service.update_payment_status(id=payment_id, status=status)
            else:
                status = payment["status"]

        await send_webhook(url=message["webhook_url"], payload={"payment_id": payment_id, "status": status})
        await msg.ack()

    except Exception:
        log.exception("Payment processing failed, retrying or moving to DLQ")
        await retry_or_dlq(message, msg)


if __name__ == "__main__":
    asyncio.run(app.run())
