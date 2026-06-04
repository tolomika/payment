import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class PaymentEntity:
    id: uuid.UUID
    amount: Decimal
    currency: str
    description: str
    metadata: dict[str, Any]
    status: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None = None


@dataclass(slots=True)
class IdempotencyRecord:
    key: str
    payment_id: uuid.UUID
    response: dict[str, Any]
    created_at: datetime


@dataclass(slots=True)
class PaymentEventEntity:
    id: uuid.UUID
    payment_id: uuid.UUID
    event_type: str
    routing_key: str
    payload: dict[str, Any]
    published: bool
    created_at: datetime
