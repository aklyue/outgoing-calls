import uuid
from datetime import datetime
from typing import TypedDict, Optional, Sequence, List

from sqlalchemy import func, select, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from api.outgoing_calls.database.postgres.crud.base import BaseCrud
from api.outgoing_calls.database.postgres.models.phone_call import PhoneCall


class PatchPhoneCall(TypedDict, total=False):
    channel_id: Optional[str]
    duration: float
    ringing_at: Optional[datetime]
    picked_up_at: datetime
    completed_at: datetime
    status: str
    code: int
    cause: str
    retry_count: int
    next_retry_at: Optional[datetime]


class PhoneCallCrud(BaseCrud[PhoneCall]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=PhoneCall, session=session)

    async def get_by_call_id(
        self,
        *,
        call_id: uuid.UUID,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Sequence[PhoneCall]:
        stmt = select(PhoneCall).where(PhoneCall.call_id == call_id)

        stmt = self._build_pagination(stmt=stmt, offset=offset, limit=limit)

        # Order by creation time so a call stays in its original position
        # even after completed_at is set later.
        stmt = stmt.order_by(PhoneCall.created_at.asc())

        result: ScalarResult[PhoneCall] = await self._session.scalars(stmt)

        return result.all()

    async def get_by_phone_number(
        self, phone_number: str, status: str
    ) -> Optional[PhoneCall]:
        stmt = select(PhoneCall).where(
            PhoneCall.phone_number == phone_number, PhoneCall.status == status
        )

        result: ScalarResult[PhoneCall] = await self._session.scalars(stmt)

        return result.one_or_none()

    async def get_by_channel_id(self, channel_id: str) -> Optional[PhoneCall]:
        stmt = select(PhoneCall).where(PhoneCall.channel_id == channel_id)

        result: ScalarResult[PhoneCall] = await self._session.scalars(stmt)

        return result.one_or_none()

    async def get_by_status(self, status: str) -> Sequence[PhoneCall]:
        stmt = select(PhoneCall).where(PhoneCall.status == status)

        result: ScalarResult[PhoneCall] = await self._session.scalars(stmt)

        return result.all()

    async def get_count_ringing(self, *, id_channels: List[str]) -> int:
        stmt = (
            select(func.count())
            .select_from(PhoneCall)
            .where(PhoneCall.status == "ringing", PhoneCall.channel_id.in_(id_channels))
        )
        result: ScalarResult[int] = await self._session.scalars(stmt)

        return result.one_or_none()
    
    async def get_count_active_by_call_id(self, call_id: uuid.UUID) -> int:
        query = (
            select(func.count(PhoneCall.id))
            .where(PhoneCall.call_id == call_id)
            .where(PhoneCall.status.in_(["in_queue", "ringing"]))
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none() or 0
    async def get_count_pending_control_calls(self, call_id: uuid.UUID) -> int:
        query = (
            select(func.count(PhoneCall.id))
            .where(PhoneCall.call_id == call_id)
            .where(PhoneCall.is_control == True)
            .where(PhoneCall.status.in_(['in_queue', 'ringing']))
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none() or 0
