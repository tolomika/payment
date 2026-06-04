from sqlalchemy.ext.asyncio import AsyncSession

from repository.idempotency import IdempotencyRepository
from repository.payment import PaymentRepository
from repository.payment_event import PaymentEventRepository
from repository.transaction import DatabaseTransaction
from service.payment.service import PaymentService


def get_payment_service(session: AsyncSession) -> PaymentService:
    return PaymentService(
        payments=PaymentRepository(session),
        idempotency_keys=IdempotencyRepository(session),
        payment_events=PaymentEventRepository(session),
        transaction=DatabaseTransaction(session),
    )
