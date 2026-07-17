from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from api.outgoing_calls.database.postgres.holder import DatabasePostgresHolder
from api.outgoing_calls.deps import DatabaseHolderMarker
from api.outgoing_calls.services import auth as auth_service
from api.outgoing_calls.deps import get_current_user
from api.outgoing_calls.schemas import UserCreate, Token, LoginRequest, UserResponse
from api.outgoing_calls.database.postgres.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=Token)
async def register(
    user_in: UserCreate, pg: DatabasePostgresHolder = Depends(DatabaseHolderMarker)
):
    if await pg.user_crud.get_by_username(user_in.username):
        raise HTTPException(status_code=400, detail="Имя пользователя занято")

    new_user = User(
        username=user_in.username,
        hashed_password=auth_service.hash_password(user_in.password),
        role=user_in.role,
    )
    await pg.user_crud.create(new_user)
    await pg.commit()
    token_data = {
        "sub": str(new_user.id),
        "username": new_user.username,
        "role": new_user.role,
    }
    return {"access_token": auth_service.create_access_token(token_data)}


@router.post("/login")
async def login(
    response: Response,
    user_in: LoginRequest,
    pg: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
):

    if not auth_service.verify_ldap_auth(user_in.username, user_in.password):
        raise HTTPException(
            status_code=401, detail="Неверный доменный логин или пароль, либо нет прав доступа"
        )

    user = await pg.user_crud.get_by_username(user_in.username)

    if not user:
        user = User(
            username=user_in.username,
            hashed_password=auth_service.hash_password(user_in.password),
            role="user", 
        )
        await pg.user_crud.create(user)
        await pg.commit()
        user = await pg.user_crud.get_by_username(user_in.username)

    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
    }

    token = auth_service.create_access_token(token_data)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return {"status": "ok"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Возвращает информацию о текущем авторизованном пользователе
    """
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role,
    }
