import uuid
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.outgoing_calls.database.postgres.crud.base import BaseCrud
from api.outgoing_calls.database.postgres.models.user import User


class UserCrud(BaseCrud[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=User, session=session)

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        # Приводим строку к UUID, если в модели используется UUID тип
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        username: Optional[str] = None,
        role: Optional[str] = None,
    ) -> List[User]:
        stmt = select(User)

        # Фильтр по частичному совпадению юзернейма (регистронезависимый)
        if username:
            stmt = stmt.where(User.username.ilike(f"%{username}%"))

        # Фильтр по точной роли
        if role:
            stmt = stmt.where(User.role == role)

        stmt = stmt.offset(offset).limit(limit).order_by(User.username)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self, username: Optional[str] = None, role: Optional[str] = None
    ) -> int:
        stmt = select(func.count()).select_from(User)

        if username:
            stmt = stmt.where(User.username.ilike(f"%{username}%"))
        if role:
            stmt = stmt.where(User.role == role)

        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def update(self, db_user: User, update_data: dict) -> User:
        for key, value in update_data.items():
            setattr(db_user, key, value)
        # SQLAlchemy подхватит изменения объекта при коммите в роутере
        return db_user
