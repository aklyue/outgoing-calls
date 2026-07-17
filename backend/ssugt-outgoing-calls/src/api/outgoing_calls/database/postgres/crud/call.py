import uuid
from datetime import datetime
from typing import TypedDict, Optional, Sequence, Dict, Any, List, Set

from sqlalchemy import select, ScalarResult, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.outgoing_calls.database.postgres.crud.base import BaseCrud
from api.outgoing_calls.database.postgres.models.call import Call
from api.outgoing_calls.database.postgres.models.phone_call import PhoneCall
from api.outgoing_calls.database.postgres.models.user import User


class PatchCall(TypedDict, total=False):
    name: str
    end_at: datetime
    retry_limit: int
    schedule: Optional[List[Dict[str, Any]]]
    tts_type: str
    categories: Set[str]
    
    # === НАСТРОЙКИ КОНТРОЛЬНОГО ЗВОНКА ===
    control_call_number: Optional[str]
    control_call_interval: int
    control_call_enabled: bool
    current_control_call_counter: int

    # === НАСТРОЙКИ EMAIL-ОТЧЕТНОСТИ ===
    email_report_address: Optional[str]
    email_report_interval: int
    email_report_enabled: bool
    current_email_report_counter: int

    # === ЧЕКБОКСЫ ТРИГГЕРОВ ===
    email_report_trigger_start: bool
    email_report_trigger_interval: bool
    email_report_trigger_final: bool


class CallCrud(BaseCrud[Call]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Call, session=session)

    async def get_by_phone_call_id(self, phone_call_id: uuid.UUID) -> Call:
        stmt = (
            select(Call)
            .join(PhoneCall, PhoneCall.call_id == Call.id)
            .where(PhoneCall.id == phone_call_id)
        )

        result: ScalarResult[Call] = await self._session.scalars(stmt)

        return result.one_or_none()

    async def get_all_with_count(
        self,
        *,
        user_id: Optional[uuid.UUID] = None,
        username: Optional[str] = None,
        call_name: Optional[str] = None,
        role: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        load_user: bool = False
    ) -> tuple[Sequence[Call], int]:
        stmt = select(Call)
        
        if username or role or load_user:
            stmt = stmt.join(User, Call.user_id == User.id)

        if user_id is not None:
            stmt = stmt.where(Call.user_id == user_id)
        
        if call_name:
            stmt = stmt.where(Call.name.ilike(f"%{call_name}%"))
            
        if username:
            stmt = stmt.where(User.username.ilike(f"%{username}%"))
            
        if role:
            stmt = stmt.where(User.role == role)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = await self._session.scalar(count_stmt) or 0

        if load_user:
            stmt = stmt.options(selectinload(Call.user))

        stmt = stmt.order_by(Call.created_at.desc())
        stmt = self._build_pagination(stmt=stmt, offset=offset, limit=limit)

        result: ScalarResult[Call] = await self._session.scalars(stmt)
        return result.all(), total_count
    
    async def get_one(self, call_id: uuid.UUID, load_user: bool = False) -> Optional[Call]:
        stmt = select(Call).where(Call.id == call_id)
        if load_user:
            stmt = stmt.options(selectinload(Call.user))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
