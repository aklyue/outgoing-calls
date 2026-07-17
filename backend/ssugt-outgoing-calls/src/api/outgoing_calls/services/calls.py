import asyncio
import os
import uuid
from datetime import datetime
from typing import List, Any, Optional, AsyncContextManager, Callable, Dict
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from api.outgoing_calls.database.postgres.crud.phone_call import PatchPhoneCall
from api.outgoing_calls.database.postgres.holder import DatabasePostgresHolder
from api.outgoing_calls.database.postgres.tools import sa_inject_holder
from api.outgoing_calls.logger import logger
from api.outgoing_calls.schemas import PhoneCallSchema, CallDailyScheduleSchema
from api.outgoing_calls.tools import (
    reformat_status_text,
    reformat_datetime_text,
    reformat_column_text,
)
from api.outgoing_calls.services.ari.manager import AriManager

DO_CALL_NEXT_TRY_SECONDS = 3
MAX_PARALLEL_CHANNELS = int(os.getenv("MAX_PARALLEL_CHANNELS", "5"))
MAX_CONCURRENT_PER_ENDPOINT = int(os.getenv("MAX_CONCURRENT_PER_ENDPOINT", "1"))
MAX_NUM_CHANNELS_OCCUPIED = int(os.getenv("MAX_NUM_CHANNELS_OCCUPIED", "2"))
PHONE_CALLS_COLUMNS = {
    "id": "№",
    "phone_number": "Телефон",
    "synthesis": "Текст синтеза",
    "ringing_at": "Начало звонка",
    "picked_up_at": "Поднял трубку",
    "completed_at": "Завершен",
    "progress": "% прослушивания",
    "status": "Статус",
    "cause": "Причина",
    "retry_count": "Кол-во попыток дозвона",
}
PHONE_CALLS_HIGHLIGHT = {
    "status": {
        "Завершено": "B7E1CD",
        "Неудачно": "F4CCCC",
        "Идет вызов": "FCE5CD",
        "В очереди": "D9D9D9",
        "неизвестно": "E6E6E6",
    }
}
PHONE_CALLS_FIXED_COLUMN_WIDTH = 60
Injector = Callable[[], AsyncContextManager[DatabasePostgresHolder]]


def reformat_phone_call(phone_call: Dict[str, Any]) -> Dict[str, Any]:
    for column in list(phone_call.keys()):
        value = phone_call[column]

        if column == "status":
            phone_call[column] = reformat_status_text(value)
        elif column in ["ringing_at", "picked_up_at", "completed_at"]:
            phone_call[column] = reformat_datetime_text(value)
        else:
            phone_call[column] = reformat_column_text(value)

    return phone_call


async def get_phone_calls(
    *,
    call_id: uuid.UUID,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    pg_holder: DatabasePostgresHolder,
) -> List[PhoneCallSchema]:
    phone_calls = await pg_holder.phone_call_crud.get_by_call_id(
        call_id=call_id, offset=offset, limit=limit
    )

    phone_calls = [phone_call.__dict__ for phone_call in phone_calls]

    for phone_call in phone_calls:
        phone_call["progress"] = None

        if phone_call["status"] != "failed":
            continue

        if not phone_call["completed_at"] or not phone_call["picked_up_at"]:
            continue

        interval = phone_call["completed_at"] - phone_call["picked_up_at"]

        interval = interval.total_seconds()

        if not interval:
            continue

        phone_call["progress"] = min(
            100.0, int(round(interval / phone_call["duration"] * 100))
        )

    return [PhoneCallSchema(**phone_call) for phone_call in phone_calls]


async def fail_ringing_phone_calls(
    *, ari_manager: AriManager, session_factory: async_sessionmaker[AsyncSession]
):
    injector = sa_inject_holder(session_factory)

    active_channels = await ari_manager.active_channels()

    id_channels = [active_channel.id for active_channel in active_channels]

    async with injector() as pg_holder:
        in_ringing_phone_calls = await pg_holder.phone_call_crud.get_by_status(
            status="ringing"
        )

        for phone_call in in_ringing_phone_calls:
            if (
                not phone_call
                or phone_call.status != "ringing"
                or not phone_call.channel_id
            ):
                continue

            if phone_call.channel_id in id_channels:
                continue

            await pg_holder.phone_call_crud.patch(
                model=phone_call,
                patch=PatchPhoneCall(
                    channel_id=None,
                    status="failed",
                    ringing_at=None,
                    completed_at=datetime.utcnow().replace(tzinfo=None),
                    cause="Не удалось отследить статус звонка",
                ),
            )
            await pg_holder.commit()


def get_current_max_channels(
    call_schedule: List[CallDailyScheduleSchema],
) -> Optional[int]:
    current_datetime = (
        datetime.utcnow()
        .astimezone(ZoneInfo("UTC"))
        .astimezone(ZoneInfo("Asia/Novosibirsk"))
    )

    weekday_token = current_datetime.strftime("%A").lower()
    current_time = current_datetime.time()

    daily = next(
        (d for d in call_schedule if d.weekday == weekday_token),
        None,
    )

    if not daily:
        return

    for slot in daily.time_ranges:
        if slot.start_time_at <= current_time < slot.end_time_at:
            return slot.max_num_channels_occupied


async def get_active_id_channels(*, ari_manager: AriManager) -> List[str]:
    active_channels = await ari_manager.active_channels()

    return [active_channel.id for active_channel in active_channels]


def is_available_call_schedule(
    *, schedule: Optional[List[Dict[str, Any]]], count_ringing: int
):
    call_schedule = (
        [CallDailyScheduleSchema(**d) for d in schedule]
        if schedule is not None
        else None
    )

    max_num_channels_occupied = MAX_NUM_CHANNELS_OCCUPIED
    if call_schedule is not None:
        max_num_channels_occupied = get_current_max_channels(call_schedule)

        if max_num_channels_occupied is None:
            return False

    if count_ringing >= max_num_channels_occupied:
        return False

    return True


async def is_wait_for_ringing_calls(
    *,
    phone_call_id: uuid.UUID,
    injector: Injector,
    concurrent_calls_semaphore: asyncio.Semaphore,
) -> bool:
    async with concurrent_calls_semaphore:
        async with injector() as pg_holder:
            phone_call = await pg_holder.phone_call_crud.get_by_id(phone_call_id)

            if not phone_call:
                logger.info(
                    "Phone call id %s not found for check calls is ringing",
                    phone_call_id,
                )

                return False

            is_ringing_calls = bool(
                await pg_holder.phone_call_crud.get_by_phone_number(
                    phone_number=phone_call.phone_number, status="ringing"
                )
            )

            if is_ringing_calls:
                # logger.info("Found ringing calls for phone call id %s", phone_call_id)

                return True

            return False


async def is_wait_for_paused_calls(
    *,
    phone_call_id: uuid.UUID,
    injector: Injector,
    concurrent_calls_semaphore: asyncio.Semaphore,
) -> bool:
    async with concurrent_calls_semaphore:
        async with injector() as pg_holder:
            call = await pg_holder.call_crud.get_by_phone_call_id(phone_call_id)

            if not call:
                logger.info(
                    "Call not found for paused calls with phone call id %s",
                    phone_call_id,
                )

                return False

            return call.is_paused


async def is_wait_for_next_retry(
    *,
    phone_call_id: uuid.UUID,
    injector: Injector,
    concurrent_calls_semaphore: asyncio.Semaphore,
) -> bool:
    async with concurrent_calls_semaphore:
        async with injector() as pg_holder:
            phone_call = await pg_holder.phone_call_crud.get_by_id(phone_call_id)

            if not phone_call:
                logger.info(
                    "Phone call not found for next retry with phone call id %s",
                    phone_call_id,
                )

                return False

            next_retry_at = phone_call.next_retry_at

            if next_retry_at and next_retry_at > datetime.utcnow().replace(tzinfo=None):
                return True

            return False


async def is_wait_for_call_schedule(
    *,
    phone_call_id: uuid.UUID,
    ari_manager: AriManager,
    injector: Injector,
    concurrent_calls_semaphore: asyncio.Semaphore,
) -> bool:
    id_channels = await get_active_id_channels(ari_manager=ari_manager)

    async with concurrent_calls_semaphore:
        async with injector() as pg_holder:
            call = await pg_holder.call_crud.get_by_phone_call_id(phone_call_id)

            if not call:
                logger.info(
                    "Call not found for paused calls with phone call id %s",
                    phone_call_id,
                )

                return False

            schedule = call.schedule.copy() if call.schedule is not None else None
            count_ringing = await pg_holder.phone_call_crud.get_count_ringing(
                id_channels=id_channels
            )

            is_available = is_available_call_schedule(
                schedule=schedule, count_ringing=count_ringing
            )

            return not is_available


def get_max_concurrent_channels() -> int:
    return min(MAX_PARALLEL_CHANNELS, MAX_CONCURRENT_PER_ENDPOINT)


async def wait_for_busy_channels(*, ari_manager: AriManager) -> None:
    max_concurrent = get_max_concurrent_channels()

    while True:
        active_channels = await ari_manager.active_channels()

        logger.info(
            "WAIT active=%d max=%d (parallel=%d endpoint=%d) ids=%s",
            len(active_channels),
            max_concurrent,
            MAX_PARALLEL_CHANNELS,
            MAX_CONCURRENT_PER_ENDPOINT,
            [c.id for c in active_channels],
        )

        if max_concurrent - len(active_channels) <= 0:
            await asyncio.sleep(DO_CALL_NEXT_TRY_SECONDS)

            continue

        break
