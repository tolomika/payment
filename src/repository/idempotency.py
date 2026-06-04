from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.payment import IdempotencyRecord
from model import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(idempotency_key: IdempotencyKey) -> IdempotencyRecord:
        return IdempotencyRecord(
            key=idempotency_key.key,
            payment_id=idempotency_key.payment_id,
            response=idempotency_key.response,
            created_at=idempotency_key.created_at,
        )

    @staticmethod
    def _to_model(idempotency_key: IdempotencyRecord) -> IdempotencyKey:
        return IdempotencyKey(
            key=idempotency_key.key,
            payment_id=idempotency_key.payment_id,
            response=idempotency_key.response,
            created_at=idempotency_key.created_at,
        )

    async def get_by_key(self, key: str) -> IdempotencyRecord | None:
        result = await self._session.execute(
            select(IdempotencyKey).where(IdempotencyKey.key == key)
        )
        idempotency_key = result.scalar_one_or_none()
        if idempotency_key is None:
            return None
        return self._to_entity(idempotency_key)

    def add(self, idempotency_key: IdempotencyRecord) -> None:
        self._session.add(self._to_model(idempotency_key))
