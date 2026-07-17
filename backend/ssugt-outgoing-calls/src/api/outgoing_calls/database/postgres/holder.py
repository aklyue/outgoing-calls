from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from api.outgoing_calls.database.postgres.crud.call import CallCrud
from api.outgoing_calls.database.postgres.crud.phone_call import PhoneCallCrud
from api.outgoing_calls.database.postgres.crud.user import UserCrud
from api.outgoing_calls.database.postgres.crud.log import AuditLogCrud


class DatabasePostgresHolder:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

        self.call_crud = CallCrud(session=self._session)
        self.phone_call_crud = PhoneCallCrud(session=self._session)
        self.user_crud = UserCrud(session)
        self.log_crud = AuditLogCrud(session)
        
    async def get_count_active_by_call_id(self, call_id: uuid.UUID) -> int:
        return await self.phone_call_crud.get_count_active_by_call_id(call_id)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
