import logging
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_conn
from core.observability import setup_sentry
from model import PaymentEvent
from service.broker.rabbit_connection import broker, declare_topology, payments_exchange

log = logging.getLogger(__name__)
setup_sentry("payments-outbox-worker")

log.info(f"Starting {__name__}")

async def drain(session: AsyncSession) -> None:
    async with session.begin():
        result = await session.execute(
            select(PaymentEvent)
            .where(PaymentEvent.published.is_(False))
            .with_for_update(skip_locked=True)
            .limit(100)
        )

        events = result.scalars().all()
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

                await session.execute(
                    update(PaymentEvent)
                    .where(PaymentEvent.id == event.id)
                    .values(
                        published=True,
                        published_at=datetime.now(timezone.utc),
                    )
                )

            except Exception:
                log.exception("Publishing failed event=%s", event.id)
                await session.execute(
                    update(PaymentEvent)
                    .where(PaymentEvent.id == event.id)
                    .values(
                        retry_count=PaymentEvent.retry_count + 1,
                        last_error="RabbitMQ publish failed",
                    )
                )
                continue

if __name__ == "__main__":
    async def main():
        async with broker:
            await declare_topology()
            while True:
                try:
                    async with db_conn.session() as session:
                        await drain(session)
                except SQLAlchemyError:
                    log.exception("Outbox drain failed, will retry")
                await asyncio.sleep(1)

    asyncio.run(main())
