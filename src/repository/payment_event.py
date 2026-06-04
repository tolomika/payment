from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.payment import PaymentEventEntity
from model import PaymentEvent


class PaymentEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(event: PaymentEvent) -> PaymentEventEntity:
        return PaymentEventEntity(
            id=event.id,
            payment_id=event.payment_id,
            event_type=event.event_type,
            routing_key=event.routing_key,
            payload=event.payload,
            published=event.published,
            created_at=event.created_at,
        )

    @staticmethod
    def _to_model(event: PaymentEventEntity) -> PaymentEvent:
        return PaymentEvent(
            id=event.id,
            payment_id=event.payment_id,
            event_type=event.event_type,
            routing_key=event.routing_key,
            payload=event.payload,
            published=event.published,
            created_at=event.created_at,
        )

    def add(self, event: PaymentEventEntity) -> None:
        self._session.add(self._to_model(event))

    async def get_unpublished_batch(self, limit: int = 100) -> list[PaymentEventEntity]:
        result = await self._session.execute(
            select(PaymentEvent)
            .where(PaymentEvent.published.is_(False))
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        return [self._to_entity(event) for event in result.scalars().all()]

    async def mark_published(self, event_id: UUID) -> None:
        await self._session.execute(
            update(PaymentEvent)
            .where(PaymentEvent.id == event_id)
            .values(
                published=True,
                published_at=datetime.now(timezone.utc),
            )
        )

    async def mark_failed(self, event_id: UUID, error: str) -> None:
        await self._session.execute(
            update(PaymentEvent)
            .where(PaymentEvent.id == event_id)
            .values(
                retry_count=PaymentEvent.retry_count + 1,
                last_error=error,
            )
        )
