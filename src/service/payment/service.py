from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from model import Payment, IdempotencyKey, PaymentEvent
from schema.payment import PaymentStatus, Currency

class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def payment_to_response(payment: Payment) -> dict[str, Any]:
        return {
            "id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "description": payment.description,
            "metadata": payment.metadata_,
            "status": payment.status,
            "webhook_url": payment.webhook_url,
            "created_at": payment.created_at,
            "processed_at": payment.processed_at,
        }

    @staticmethod
    def payment_to_create_response(payment: Payment) -> dict[str, Any]:
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

        result = await self.session.execute(
            select(Payment).where(Payment.id == parsed_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            return None
        return self.payment_to_response(payment)

    async def get_idempotency(self, idempotency_key: str) -> IdempotencyKey | None:
        idempotency = await self.session.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.key == idempotency_key
            )
        )
        return idempotency.scalar_one_or_none()

    async def create_payment(
        self,
        amount: Decimal,
        currency: Currency,
        description: str,
        metadata: dict,
        webhook_url: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        async with self.session.begin():
            idempotency = await self.get_idempotency(idempotency_key)
            if idempotency:
                return idempotency.response

            payment_id = uuid.uuid4()
            created_at = datetime.now(timezone.utc)
            payment = Payment(
                id=payment_id,
                amount=amount,
                currency=currency.value,
                description=description,
                metadata_=metadata,
                status=PaymentStatus.pending.value,
                webhook_url=webhook_url,
                created_at=created_at,
            )

            self.session.add(payment)

            response = self.payment_to_create_response(payment)

            event = PaymentEvent(
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

            self.session.add(event)

            idem = IdempotencyKey(
                key=idempotency_key,
                payment_id=payment_id,
                response={
                    "payment_id": str(response["payment_id"]),
                    "status": response["status"],
                    "created_at": response["created_at"].isoformat(),
                },
                created_at=created_at,
            )

            self.session.add(idem)

            await self.session.flush()

            return response

    async def update_payment_status(self, id: str, status: PaymentStatus | str) -> None:
        payment_id = uuid.UUID(str(id))
        status_value = status.value if isinstance(status, PaymentStatus) else status
        await self.session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=status_value,
                processed_at=datetime.now(timezone.utc),
            )
        )
        await self.session.commit()
