from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError

from api.outgoing_calls.services.auth import SECRET_KEY, ALGORITHM
from api.outgoing_calls.database.postgres.holder import DatabasePostgresHolder

if TYPE_CHECKING:
    from api.outgoing_calls.database.postgres.models.user import User


class ApiClientMarker:
    pass


class DatabaseEngineMarker:
    pass


class DatabaseSessionFactoryMarker:
    pass


class DatabaseHolderMarker:
    pass


class IamTokenFetcherMarker:
    pass


class RabbitBrokerMarker:
    pass


async def get_current_user(
    request: Request,
    pg: DatabasePostgresHolder = Depends(DatabaseHolderMarker)
) -> "User":
    # 1. Достаем токен напрямую из куки по ключу 'access_token'
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Сессия отсутствует (кука не найдена)"
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise JWTError()
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Невалидный токен или срок действия истек"
        )

    # 2. Ищем пользователя. Сначала по username, потом по email
    user = await pg.user_crud.get_by_id(user_id)
        
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Пользователь не найден"
        )
        
    return user