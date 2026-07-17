from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from api.outgoing_calls.database.postgres.holder import DatabasePostgresHolder
from api.outgoing_calls.deps import DatabaseHolderMarker, get_current_user
from api.outgoing_calls.schemas import UserResponse, UserUpdate, UserPaginationResponse
from api.outgoing_calls.database.postgres.models.user import User
from api.outgoing_calls.services import auth as auth_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=UserPaginationResponse)
async def get_users(
    offset: int = 0,
    limit: int = 50,
    username: Optional[str] = None,
    role: Optional[str] = None,
    pg: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    users = await pg.user_crud.get_all(
        offset=offset, limit=limit, username=username, role=role
    )
    total = await pg.user_crud.count(username=username, role=role)

    return {"items": users, "total": total, "offset": offset, "limit": limit}


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    pg: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
    current_user: User = Depends(get_current_user),
):
    db_user = await pg.user_crud.get_by_id(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if db_user.role == "owner" and current_user.role != "owner":
        raise HTTPException(
            status_code=403, detail="Нельзя редактировать владельца системы"
        )

    is_privileged = current_user.role in ["admin", "owner"]
    if not is_privileged and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    update_data = user_in.model_dump(exclude_unset=True)

    if "role" in update_data and str(current_user.id) == user_id:
        if update_data["role"] != current_user.role:
            raise HTTPException(
                status_code=400, detail="Вы не можете изменить собственную роль"
            )

    if update_data.get("role") == "owner" and current_user.role != "owner":
        raise HTTPException(
            status_code=403, detail="Только владелец может назначать других суперюзеров"
        )


    if "password" in update_data:
        update_data["hashed_password"] = auth_service.hash_password(
            update_data.pop("password")
        )

    if "role" in update_data and not is_privileged:
        update_data.pop("role")

    updated_user = await pg.user_crud.update(db_user, update_data)
    await pg.commit()

    return updated_user
