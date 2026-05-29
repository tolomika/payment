import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Numeric, String, UUID, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(), nullable=False)
    description: Mapped[str] = mapped_column(String(512), default="")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB)
    status: Mapped[str] = mapped_column(String(16), index=True)
    webhook_url: Mapped[str] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    payment_events: Mapped[list["PaymentEvent"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )

    idempotency_record: Mapped["IdempotencyKey"] = relationship(
        back_populates="payment",
        uselist=False,
        cascade="all, delete-orphan",
    )
