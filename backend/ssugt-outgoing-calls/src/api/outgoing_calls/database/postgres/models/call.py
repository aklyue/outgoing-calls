import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Set

from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import String, ForeignKey, Boolean, Integer  # Добавлен ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from api.outgoing_calls.database.postgres.models.base import BaseModel

if TYPE_CHECKING:
    from api.outgoing_calls.database.postgres.models.phone_call import PhoneCall
    from api.outgoing_calls.database.postgres.models.user import User  # Добавлено для типизации


class Call(BaseModel):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Связь с пользователем
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True
    )

    name: Mapped[str]

    created_at: Mapped[datetime]

    is_paused: Mapped[bool]

    retry_limit: Mapped[int]

    schedule: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB)

    tts_type: Mapped[str]

    categories: Mapped[Set[str]] = mapped_column(ARRAY(String))
    
    
    # === НАСТРОЙКИ КОНТРОЛЬНОГО ЗВОНКА ===
    control_call_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    control_call_interval: Mapped[int] = mapped_column(Integer, default=50)
    control_call_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    current_control_call_counter: Mapped[int] = mapped_column(Integer, default=0)

    # === НАСТРОЙКИ EMAIL-ОТЧЕТНОСТИ ===
    email_report_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email_report_interval: Mapped[int] = mapped_column(Integer, default=100)
    email_report_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    current_email_report_counter: Mapped[int] = mapped_column(Integer, default=0)

    # === ЧЕКБОКСЫ ТРИГГЕРОВ (ОТПРАВКА ОТЧЕТОВ) ===
    email_report_trigger_start: Mapped[bool] = mapped_column(Boolean, default=False)
    email_report_trigger_interval: Mapped[bool] = mapped_column(Boolean, default=False)
    email_report_trigger_final: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship к пользователю
    user: Mapped["User"] = relationship("User", back_populates="calls")

    phone_calls: Mapped[List["PhoneCall"]] = relationship(
        "PhoneCall", lazy="selectin", cascade="all, delete-orphan"
    )

    @hybrid_property
    def phone_calls_count(self):
        return len(self.phone_calls)
