import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.payment import PaymentEntity
from model import Payment
from schema.payment import PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(payment: Payment) -> PaymentEntity:
        return PaymentEntity(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.metadata_,
            status=payment.status,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )

    @staticmethod
    def _to_model(payment: PaymentEntity) -> Payment:
        return Payment(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata_=payment.metadata,
            status=payment.status,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )

    async def get_by_id(self, payment_id: uuid.UUID) -> PaymentEntity | None:
        result = await self._session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            return None
        return self._to_entity(payment)

    def add(self, payment: PaymentEntity) -> None:
        self._session.add(self._to_model(payment))

    async def update_status(
        self,
        payment_id: uuid.UUID,
        status: PaymentStatus | str,
    ) -> None:
        status_value = status.value if isinstance(status, PaymentStatus) else status
        await self._session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=status_value,
                processed_at=datetime.now(timezone.utc),
            )
        )
