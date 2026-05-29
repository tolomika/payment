from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import Field, BaseModel, HttpUrl

from schema.payment import Currency, PaymentStatus


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0, description="Payment amount")
    currency: Currency = Field(description="Payment currency")
    description: str = Field(default="", description="Short payment description")
    metadata: dict = Field(default_factory=dict, description="Additional JSON data")
    webhook_url: HttpUrl = Field(description="Webhook callback URL")


class PaymentWebhookRequest(BaseModel):
    id: str = Field(description="Payment ID")
    status: PaymentStatus = Field(description="Payment status")


class PaymentCreateResponse(BaseModel):
    payment_id: UUID = Field(description="Unique payment ID")
    status: PaymentStatus = Field(description="Payment status")
    created_at: datetime = Field(description="Creation time")


class PaymentStatusResponse(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Unique payment ID")
    amount: Decimal = Field(gt=0, description="Payment amount")
    currency: Currency = Field(description="Payment currency")
    description: str = Field(default="", description="Short payment description")
    metadata: dict = Field(default_factory=dict, description="Additional JSON data")
    status: PaymentStatus = Field(default=PaymentStatus.pending.value, description="Payment status")
    webhook_url: HttpUrl = Field(description="Webhook callback URL")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation time")
    processed_at: datetime | None = Field(default=None, description="Processing time")
