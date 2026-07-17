import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from api.outgoing_calls.database.postgres.models.base import BaseModel


class PhoneCall(BaseModel):
    __tablename__ = "phone_calls"
    __table_args__ = (
        Index(
            "unique_ringing_call_per_number",
            "phone_number",
            unique=True,
            postgresql_where=text("status = 'ringing'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    call_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    is_control: Mapped[bool] = mapped_column(Boolean, default=False)

    channel_id: Mapped[Optional[str]] = mapped_column(unique=True, index=True)

    phone_number: Mapped[str] = mapped_column(index=True)

    synthesis: Mapped[str]

    duration: Mapped[Optional[float]]

    ringing_at: Mapped[Optional[datetime]]

    picked_up_at: Mapped[Optional[datetime]]

    completed_at: Mapped[Optional[datetime]]

    status: Mapped[str]

    code: Mapped[Optional[int]]

    cause: Mapped[Optional[str]]
    """Состояние звонка"""

    next_retry_at: Mapped[Optional[datetime]]

    retry_count: Mapped[int] = mapped_column(default=0)
