from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.outgoing_calls.database.postgres.models.log import AuditLog
from typing import Sequence, Optional



class AuditLogCrud:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def create(self, log_data: AuditLog) -> AuditLog:
        self._session.add(log_data)
        return log_data

    async def count(
        self,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        action_type: Optional[str] = None,
    ) -> int:
        stmt = select(func.count()).select_from(AuditLog)

        # Применяем фильтры
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if username:
            # ilike делает поиск нечувствительным к регистру: "admin" найдет "Admin"
            stmt = stmt.where(AuditLog.username.ilike(f"%{username}%"))
        if action_type:
            stmt = stmt.where(AuditLog.action_type == action_type)

        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_all(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        action_type: Optional[str] = None,
    ) -> Sequence[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())

        # Применяем те же фильтры, что и в count
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if username:
            stmt = stmt.where(AuditLog.username.ilike(f"%{username}%"))
        if action_type:
            stmt = stmt.where(AuditLog.action_type == action_type)

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self._session.execute(stmt)
        return result.scalars().all()
