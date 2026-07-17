import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from api.outgoing_calls.database.postgres.models.base import BaseModel

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    # Используем uuid.UUID как в модели User
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    user_id: Mapped[Optional[str]] = mapped_column(index=True, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(nullable=True)
    
    action_type: Mapped[str] = mapped_column(index=True, nullable=False)
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # JSONB для Postgres — это топ для payload
    payload: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    
    ip_address: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)