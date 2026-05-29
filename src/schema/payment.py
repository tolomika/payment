from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from uuid import UUID, uuid4
from decimal import Decimal

from datetime import datetime, timezone


class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4, description="Unique payment ID")
    amount: Decimal = Field(gt=0, description="Payment amount")
    currency: Currency = Field(description="Payment currency")
    description: str = Field(default="", description="Short payment description")
    metadata: dict = Field(default_factory=dict, description="Additional JSON data")
    status: str = Field(description="Payment status")
    webhook_url: HttpUrl = Field(description="Webhook callback URL")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation time")
    processed_at: datetime | None = Field(default=None, description="Processing time")
