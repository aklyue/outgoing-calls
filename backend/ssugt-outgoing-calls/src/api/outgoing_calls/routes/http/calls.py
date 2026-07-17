import asyncio
import uuid
from datetime import datetime
from typing import Optional, List, Literal, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from faststream.rabbit import RabbitBroker
from starlette.responses import StreamingResponse

from api.outgoing_calls.logger import logger

from api.outgoing_calls.database.postgres.holder import DatabasePostgresHolder
from api.outgoing_calls.database.postgres.models.call import Call
from api.outgoing_calls.database.postgres.models.phone_call import PhoneCall
from api.outgoing_calls.deps import (
    DatabaseHolderMarker,
    RabbitBrokerMarker,
    get_current_user,
)
from api.outgoing_calls.schemas import (
    OutgoingCallsSchema,
    CallSchema,
    PhoneCallSchema,
    PatchCallSchema,
)

from api.outgoing_calls.database.postgres.models.user import User
from api.outgoing_calls.services.calls import (
    get_phone_calls,
    PHONE_CALLS_COLUMNS,
    reformat_phone_call,
    PHONE_CALLS_HIGHLIGHT,
    PHONE_CALLS_FIXED_COLUMN_WIDTH,
)
from api.outgoing_calls.tools import normalize_phone, json_to_xlsx, get_phone_category

if TYPE_CHECKING:
    from api.outgoing_calls.database.postgres.models.user import User

PHONE_CATEGORIES_MAPPING = {
    "ru_mobile_numbers": "российский мобильный",
    "ru_city_numbers": "российский городской",
    "international_numbers": "международный",
}
router = APIRouter()


@router.get("/calls/")
async def retrieve_calls(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    call_name: Optional[str] = None,
    username: Optional[str] = None,
    role: Optional[str] = None,
    pg_holder: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
    current_user: User = Depends(get_current_user),
):
    is_privileged = current_user.role in ["admin", "owner"]

    filter_user_id = None if is_privileged else current_user.id

    search_username = username if is_privileged else None
    search_role = role if is_privileged else None

    calls, total = await pg_holder.call_crud.get_all_with_count(
        offset=offset,
        limit=limit,
        user_id=filter_user_id,
        username=search_username,
        call_name=call_name,
        role=search_role,
        load_user=True,
    )

    return {"items": calls, "total": total, "offset": offset, "limit": limit}


@router.patch("/calls/{call_id}", response_model=CallSchema)
async def patch_call(
    call_id: uuid.UUID,
    call_patch: PatchCallSchema,
    pg_holder: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
    user: "User" = Depends(get_current_user),
):
    call_obj = await pg_holder.call_crud.get_one(call_id, load_user=True)

    if not call_obj:
        raise HTTPException(status_code=404, detail="Call not found")
    
    can_edit = user.role in ["admin", "owner"] or call_obj.user_id == user.id

    if not can_edit:
        raise HTTPException(status_code=403, detail="Access denied to this call")

    update_data = call_patch.model_dump(exclude_unset=True)
    await pg_holder.call_crud.patch(model=call_obj, patch=update_data)

    await pg_holder.commit()

    return call_obj


@router.delete("/calls/{call_id}", response_model=CallSchema)
async def delete_call(
    call_id: uuid.UUID,
    pg_holder: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
    user: "User" = Depends(get_current_user),
):
    call_obj = await pg_holder.call_crud.get_one(call_id, load_user=True)

    if not call_obj:
        raise HTTPException(status_code=404, detail="Call not found")
    
    can_delete = user.role in ["admin", "owner"] or call_obj.user_id == user.id

    if not can_delete:
        raise HTTPException(status_code=403, detail="Access denied")

    await pg_holder.call_crud.delete(model=call_obj)
    await pg_holder.commit()

    return call_obj


@router.get("/phone_calls/{call_id}", response_model=List[PhoneCallSchema])
async def retrieve_phone_calls(
    call_id: uuid.UUID,
    format: Literal["json", "xlsx"] = Query(default="json"),
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    pg_holder: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
    user: "User" = Depends(get_current_user),
):
    # Сначала проверяем, есть ли доступ к основному звонку
    call = await pg_holder.call_crud.get_by_id(call_id)
    
    can_view = call and (user.role in ["admin", "owner"] or call.user_id == user.id)
    
    if not can_view:
        raise HTTPException(status_code=404, detail="Call not found or access denied")

    phone_calls = await get_phone_calls(
        call_id=call_id, offset=offset, limit=limit, pg_holder=pg_holder
    )

    response = phone_calls
    if format == "xlsx":
        call = await pg_holder.call_crud.get_by_id(call_id)

        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        data = [
            reformat_phone_call({**phone_call.model_dump(mode="json"), "id": index + 1})
            for index, phone_call in enumerate(phone_calls)
        ]

        output = json_to_xlsx(
            title=call.name,
            data=data,
            columns=PHONE_CALLS_COLUMNS,
            highlight=PHONE_CALLS_HIGHLIGHT,
            fixed_column_width=PHONE_CALLS_FIXED_COLUMN_WIDTH,
        )

        response = StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="phone_calls_{call_id}.xlsx"'
            },
        )

    return response


@router.post("/calls/")
async def do_calls(
    out_calls: OutgoingCallsSchema,
    broker: RabbitBroker = Depends(RabbitBrokerMarker),
    pg_holder: DatabasePostgresHolder = Depends(DatabaseHolderMarker),
    user: "User" = Depends(get_current_user),
):
    utc_now = datetime.utcnow().replace(tzinfo=None)
    # Привязываем создаваемый звонок к текущему юзеру
    call = await pg_holder.call_crud.create(
        model=Call(
            name=out_calls.name,
            created_at=utc_now,
            is_paused=out_calls.is_paused,
            retry_limit=out_calls.retry_limit,
            schedule=(
                [d.model_dump(mode="json") for d in out_calls.schedule]
                if out_calls.schedule is not None
                else None
            ),
            tts_type=out_calls.tts_type,
            categories=out_calls.categories,
            user_id=user.id,  # ПРИВЯЗКА
            
            # === СЮДА ДОБАВЛЯЕМ ПРИ СОЗДАНИИ ===
            control_call_number=out_calls.control_call_number,
            control_call_interval=out_calls.control_call_interval,
            control_call_enabled=out_calls.control_call_enabled,
            
            email_report_address=out_calls.email_report_address,
            email_report_interval=out_calls.email_report_interval,
            email_report_enabled=out_calls.email_report_enabled,
            
            email_report_trigger_start=out_calls.email_report_trigger_start,
            email_report_trigger_interval=out_calls.email_report_trigger_interval,
            email_report_trigger_final=out_calls.email_report_trigger_final,
        ),
    )
    logger.info("[TRACE START] call_id=%s", call.id)

    current_utc = datetime.utcnow()
    phone_calls = []
    publish_messages = []

    control_phone_number: Optional[str] = None
    if out_calls.control_call_enabled and out_calls.control_call_number:
        control_phone_number = normalize_phone(out_calls.control_call_number)
        if not control_phone_number:
            raise HTTPException(
                status_code=400,
                detail="Invalid control_call_number",
            )

    regular_counter = 0

    for out_call in out_calls.calls:
        phone_number = normalize_phone(out_call.phone_number)

        if not phone_number:
            await pg_holder.phone_call_crud.create(
                model=PhoneCall(
                    call_id=call.id,
                    phone_number=out_call.phone_number,
                    synthesis=out_call.text,
                    status="failed",
                    cause="Не удалось преобразовать номер телефона",
                    created_at=current_utc.replace(tzinfo=None),
                    completed_at=current_utc.replace(tzinfo=None),
                )
            )
            continue

        category = get_phone_category(phone_number)

        if category not in out_calls.categories:
            category = PHONE_CATEGORIES_MAPPING.get(category, "неизвестная")

            await pg_holder.phone_call_crud.create(
                model=PhoneCall(
                    call_id=call.id,
                    phone_number=out_call.phone_number,
                    synthesis=out_call.text,
                    status="failed",
                    cause=f"Категория «{category}» номера телефона неподходящая",
                    created_at=current_utc.replace(tzinfo=None),
                    completed_at=current_utc.replace(tzinfo=None),
                )
            )
            continue

        out_call.phone_number = phone_number

        phone_call = await pg_holder.phone_call_crud.create(
            model=PhoneCall(
                call_id=call.id,
                phone_number=out_call.phone_number,
                synthesis=out_call.text,
                status="in_queue",
                created_at=current_utc.replace(tzinfo=None),
                is_control=False,
            )
        )
        phone_calls.append(phone_call)
        publish_messages.append(
            {"phone_call_id": str(phone_call.id)}
        )
        regular_counter += 1

        if (
            control_phone_number
            and out_calls.control_call_interval > 0
            and regular_counter >= out_calls.control_call_interval
        ):
            regular_counter = 0
            control_phone_call = await pg_holder.phone_call_crud.create(
                model=PhoneCall(
                    call_id=call.id,
                    phone_number=control_phone_number,
                    synthesis="[CONTROL] Контрольный звонок. Проверка работоспособности каналов связи.",
                    status="in_queue",
                    created_at=current_utc.replace(tzinfo=None),
                    is_control=True,
                )
            )
            phone_calls.append(control_phone_call)
            publish_messages.append(
                {"phone_call_id": str(control_phone_call.id), "is_control": True}
            )

    await pg_holder.commit()

    tasks = [
        asyncio.create_task(
            broker.publish(
                message,
                exchange="calls",
                routing_key="call",
            )
        )
        for message in publish_messages
    ]
    
    # === ТРИГГЕР ОТЧЕТНОСТИ ПРИ СТАРТЕ ===
    if out_calls.email_report_enabled and out_calls.email_report_trigger_start:
        await broker.publish(
            {
                "call_id": str(call.id),
                "trigger": "start",
                "email": out_calls.email_report_address
            },
            exchange="reports",
            routing_key="send_email"
        )

    await pg_holder.commit()
    return {"status": "in_queue", "call_id": call.id}
