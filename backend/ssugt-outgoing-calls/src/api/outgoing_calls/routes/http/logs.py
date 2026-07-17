from fastapi import APIRouter, Depends, Request
from api.outgoing_calls.database.postgres.models.log import AuditLog
from api.outgoing_calls.deps import DatabaseHolderMarker
from api.outgoing_calls.schemas import AuditLogCreate
from api.outgoing_calls.database.postgres.holder import DatabasePostgresHolder

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from api.outgoing_calls.database.postgres.holder import DatabasePostgresHolder
from api.outgoing_calls.deps import DatabaseHolderMarker, get_current_user
from api.outgoing_calls.schemas import AuditLogRead, AuditLogPaginationResponse
from api.outgoing_calls.database.postgres.models.user import User
from datetime import datetime, timezone, timedelta

router = APIRouter()


@router.post("/")
async def create_audit_log(
    log_in: AuditLogCreate,
    request: Request,
    pg: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
    current_user: Optional[User] = Depends(get_current_user),
):

    NSK_TZ = timezone(timedelta(hours=7))
    
    user_id = str(current_user.id) if current_user else None
    username = current_user.username if current_user else "Guest"
    new_log = AuditLog(
        user_id=user_id,
        username=username,
        action_type=log_in.action_type,
        action_description=log_in.action_description,
        payload=log_in.payload,
        ip_address=request.client.host,
        created_at=datetime.now(NSK_TZ).replace(tzinfo=None),
    )

    pg.log_crud.create(new_log)
    await pg.commit()

    return {"status": "ok"}


@router.get("/", response_model=AuditLogPaginationResponse)
async def retrieve_audit_logs(
    offset: int = 0,
    limit: int = 50,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    action_type: Optional[str] = None,
    pg_holder: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
    current_user: User = Depends(get_current_user),
):
    effective_user_id = user_id
    effective_username = username

    if current_user.role == "owner":
        pass

    elif current_user.role == "admin":
        pass

    else:
        effective_user_id = str(current_user.id)
        effective_username = None

    logs = await pg_holder.log_crud.get_all(
        offset=offset,
        limit=limit,
        user_id=effective_user_id,
        username=effective_username,
        action_type=action_type,
    )

    total_count = await pg_holder.log_crud.count(
        user_id=effective_user_id, username=effective_username, action_type=action_type
    )

    return {"items": logs, "total": total_count, "offset": offset, "limit": limit}
