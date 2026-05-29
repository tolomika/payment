import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from model.base import Base


class PaymentEvent(Base):
    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    routing_key: Mapped[str] = mapped_column(String(128), index=True)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id"),
        index=True,
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    retry_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    last_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    payment: Mapped["Payment"] = relationship(
        back_populates="payment_events",
    )
