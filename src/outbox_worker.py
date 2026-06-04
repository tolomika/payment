import logging
import asyncio

from sqlalchemy.exc import SQLAlchemyError

from core.database import db_conn
from service.broker.rabbit_connection import broker, declare_topology, payments_exchange
from service.payment.factory import get_payment_service
from service.payment.service import PaymentService

log = logging.getLogger(__name__)

log.info(f"Starting {__name__}")


async def drain(
    payment_service: PaymentService,
) -> None:
    events = await payment_service.get_unpublished_events(limit=100)
    for event in events:
        try:
            await broker.publish(
                message=event.payload,
                exchange=payments_exchange,
                routing_key=event.routing_key,
                persist=True,
                message_id=str(event.id),
                message_type=event.event_type,
            )

            log.info(
                "Published event to queue",
                extra={
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "routing_key": event.routing_key,
                },
            )

            await payment_service.mark_as_published(event_id=event.id)

        except Exception:
            log.exception("Publishing failed event=%s", event.id)
            await payment_service.mark_failed(event.id, "RabbitMQ publish failed")
            continue

if __name__ == "__main__":
    async def main():
        async with broker:
            await declare_topology()
            while True:
                try:
                    async with db_conn.session() as session:
                        payment_service = get_payment_service(session)
                        await drain(payment_service=payment_service)
                except SQLAlchemyError:
                    log.exception("Outbox drain failed, will retry")
                await asyncio.sleep(1)

    asyncio.run(main())
