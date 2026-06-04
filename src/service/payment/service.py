from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import Any

from domain.payment import IdempotencyRecord, PaymentEntity, PaymentEventEntity
from repository.idempotency import IdempotencyRepository
from repository.payment import PaymentRepository
from repository.payment_event import PaymentEventRepository
from repository.transaction import DatabaseTransaction
from schema.payment import PaymentStatus, Currency


class PaymentService:
    def __init__(
        self,
        payments: PaymentRepository,
        idempotency_keys: IdempotencyRepository,
        payment_events: PaymentEventRepository,
        transaction: DatabaseTransaction,
    ) -> None:
        self.payments = payments
        self.idempotency_keys = idempotency_keys
        self.payment_events = payment_events
        self.transaction = transaction

    @staticmethod
    def payment_to_response(payment: PaymentEntity) -> dict[str, Any]:
        return {
            "id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "description": payment.description,
            "metadata": payment.metadata,
            "status": payment.status,
            "webhook_url": payment.webhook_url,
            "created_at": payment.created_at,
            "processed_at": payment.processed_at,
        }

    @staticmethod
    def payment_to_create_response(payment: PaymentEntity) -> dict[str, Any]:
        return {
            "payment_id": payment.id,
            "status": payment.status,
            "created_at": payment.created_at,
        }

    async def get_payment(self, payment_id: str) -> dict[str, Any] | None:
        try:
            parsed_id = uuid.UUID(str(payment_id))
        except ValueError:
            return None

        payment = await self.payments.get_by_id(parsed_id)
        if not payment:
            return None
        return self.payment_to_response(payment)

    async def get_idempotency(self, idempotency_key: str) -> IdempotencyRecord | None:
        return await self.idempotency_keys.get_by_key(idempotency_key)

    async def create_payment(
        self,
        amount: Decimal,
        currency: Currency,
        description: str,
        metadata: dict,
        webhook_url: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        async with self.transaction.begin():
            idempotency = await self.get_idempotency(idempotency_key)
            if idempotency:
                return idempotency.response

            payment_id = uuid.uuid4()
            created_at = datetime.now(timezone.utc)
            payment = PaymentEntity(
                id=payment_id,
                amount=amount,
                currency=currency.value,
                description=description,
                metadata=metadata,
                status=PaymentStatus.pending.value,
                webhook_url=webhook_url,
                created_at=created_at,
            )

            self.payments.add(payment)

            response = self.payment_to_create_response(payment)

            event = PaymentEventEntity(
                id=uuid.uuid4(),
                payment_id=payment_id,
                event_type="payment.new",
                routing_key="payments.new",
                payload={
                    "id": str(payment_id),
                    "amount": str(amount),
                    "currency": currency.value,
                    "description": description,
                    "metadata": metadata,
                    "status": PaymentStatus.pending.value,
                    "webhook_url": webhook_url,
                    "created_at": created_at.isoformat(),
                },
                published=False,
                created_at=created_at,
            )

            self.payment_events.add(event)

            idem = IdempotencyRecord(
                key=idempotency_key,
                payment_id=payment_id,
                response={
                    "payment_id": str(response["payment_id"]),
                    "status": response["status"],
                    "created_at": response["created_at"].isoformat(),
                },
                created_at=created_at,
            )

            self.idempotency_keys.add(idem)

            await self.transaction.flush()

            return response

    async def update_payment_status(self, id: str, status: PaymentStatus | str) -> None:
        payment_id = uuid.UUID(str(id))
        await self.payments.update_status(payment_id, status)
        await self.transaction.commit()

    async def get_unpublished_events(self, limit: int | None=None) -> list[PaymentEventEntity]:
        return await self.payment_events.get_unpublished_batch(limit=limit)

    async def mark_as_published(self, event_id: uuid.UUID):
        await self.payment_events.mark_published(event_id=event_id)

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        await self.payment_events.mark_failed(event_id=event_id, error=error)
