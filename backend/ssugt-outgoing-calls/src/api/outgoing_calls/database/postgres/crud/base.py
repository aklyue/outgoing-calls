from abc import ABC
from typing import Any, TypeVar, Generic, TypedDict, Optional, overload, Sequence, Union

from sqlalchemy import select, ScalarResult, Select, Selectable, CTE
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query

from api.outgoing_calls.database.postgres.models.base import BaseModel

Model = TypeVar("Model", bound=BaseModel)
SelectableQuery = Union[Query, Selectable, CTE]


class BaseCrud(ABC, Generic[Model]):

    def __init__(self, *, model: type[Model], session: AsyncSession) -> None:
        self._model = model
        self._session = session

    def _build_pagination(
        self,
        *,
        stmt: SelectableQuery,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> SelectableQuery:
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return stmt

    async def get_by_id(self, id: Any) -> Optional[Model]:
        return await self._session.get(self._model, id)

    async def get_all(
        self, *, offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Sequence[Model]:
        stmt = select(self._model)

        stmt = self._build_pagination(stmt=stmt, offset=offset, limit=limit)

        result: ScalarResult[Model] = await self._session.scalars(stmt)

        return result.all()

    async def create(self, model: Model) -> Model:
        self._session.add(model)
        await self._session.flush()

        return model

    @overload
    async def patch(self, *, model: Model, patch: TypedDict) -> Model: ...

    @overload
    async def patch(self, *, id: Any, patch: TypedDict) -> Optional[Model]: ...

    async def patch(
        self,
        *,
        id: Any = None,
        model: Model = None,
        patch: TypedDict,
        user_id: Any = None,
    ) -> Optional[Model]:
        if model is None:
            model = await self.get_by_id(id=id)
            if not model:
                return None

        if user_id is not None and hasattr(model, "user_id"):
            if model.user_id != user_id:
                return None

        for field in model.__mapper__.attrs.keys():
            if field in patch:
                setattr(model, field, patch[field])

        await self._session.flush()
        return model

    @overload
    async def delete(self, *, model: Model) -> Model: ...

    @overload
    async def delete(self, *, id: Any) -> Model | None: ...

    async def delete(
        self, *, id: Any = None, model: Model = None, user_id: Any = None
    ) -> Model | None:
        if model is None:
            model = await self.get_by_id(id)
            if not model:
                return None
        
        if user_id is not None and hasattr(model, "user_id"):
            if model.user_id != user_id:
                return None

        await self._session.delete(model)
        await self._session.flush()
        return model
