from typing import Annotated

from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.database import db_conn

from service.payment.factory import get_payment_service
from api.v1.payment.schema import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentStatusResponse,
    PaymentWebhookRequest,
)

router = APIRouter()

@router.post("/payments", status_code=status.HTTP_202_ACCEPTED, response_model=PaymentCreateResponse)
async def create_payment(
    session: Annotated[AsyncSession, Depends(db_conn.get_db)],
    payload: PaymentCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> dict:
    payment_service = get_payment_service(session)
    return await payment_service.create_payment(
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        metadata=payload.metadata,
        webhook_url=str(payload.webhook_url),
        idempotency_key=idempotency_key,
    )

@router.get("/payments/{payment_id}", status_code=status.HTTP_200_OK, response_model=PaymentStatusResponse)
async def get_payment(
        session: Annotated[AsyncSession, Depends(db_conn.get_db)],
        payment_id: str,
) -> dict:
    payment_service = get_payment_service(session)
    payment = await payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return payment

@router.post("/payment/webhook", status_code=status.HTTP_202_ACCEPTED)
async def send_payment_status_webhook(
        session: Annotated[AsyncSession, Depends(db_conn.get_db)],
        payload: PaymentWebhookRequest,
) -> bool:
    payment_service = get_payment_service(session)
    await payment_service.update_payment_status(id=payload.id, status=payload.status)
    return True
