import asyncio
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import aiohttp
from faststream import Context
from faststream.rabbit import (
    RabbitRouter,
    RabbitQueue,
    RabbitExchange,
    ExchangeType,
    RabbitBroker,
    RabbitMessage,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from api.outgoing_calls.database.postgres.crud.phone_call import PatchPhoneCall
from api.outgoing_calls.database.postgres.tools import sa_inject_holder
from api.outgoing_calls.logger import logger
from api.outgoing_calls.services.ari.manager import AriManager
from api.outgoing_calls.services.calls import (
    is_wait_for_paused_calls,
    is_wait_for_next_retry,
    is_wait_for_ringing_calls,
    is_wait_for_call_schedule,
    wait_for_busy_channels,
    get_active_id_channels,
    is_available_call_schedule,
)
from api.outgoing_calls.services.control_call_queue import ControlCallQueueGate
from api.outgoing_calls.services.storage import upload_audio_file
from api.outgoing_calls.services.tts.manager import is_stt_available, synthesize_speech
from api.outgoing_calls.services.tts.yandex import IamTokenFetcher

CALL_RETRY_DELAYED_MESSAGE_IN_SECONDS = int(
    os.getenv("CALL_RETRY_DELAYED_MESSAGE_IN_SECONDS", 5)
)
CALL_RETRY_DELAYED_MESSAGE = CALL_RETRY_DELAYED_MESSAGE_IN_SECONDS * 1000
CALL_NEXT_TRY_IN_SECONDS = int(os.getenv("CALL_NEXT_TRY_IN_SECONDS", "5"))
amqp_router = RabbitRouter()
calls_exchange = RabbitExchange(
    "calls",
    type=ExchangeType.X_DELAYED_MESSAGE,
    arguments={"x-delayed-type": "direct"},
)
call_queue = RabbitQueue("call", durable=True)


# === 1. ОСНОВНОЙ ПОДПИСЧИК ДЛЯ ОБЫЧНЫХ ЗВОНКОВ ===
@amqp_router.subscriber(call_queue)
async def do_call(
    message: RabbitMessage,
    broker: RabbitBroker = Context(),
    ari_manager: AriManager = Context(),
    session_factory: async_sessionmaker[AsyncSession] = Context(),
    api_client: aiohttp.ClientSession = Context(),
    calls_locker: asyncio.Lock = Context(),
    concurrent_calls_semaphore: asyncio.Semaphore = Context(),
    fetch_iam_token: IamTokenFetcher = Context(),
    control_call_queue_gate: ControlCallQueueGate = Context(),
):
    await _process_call(
        message=message,
        broker=broker,
        ari_manager=ari_manager,
        session_factory=session_factory,
        api_client=api_client,
        calls_locker=calls_locker,
        concurrent_calls_semaphore=concurrent_calls_semaphore,
        fetch_iam_token=fetch_iam_token,
        control_call_queue_gate=control_call_queue_gate,
    )


# === 3. ЕДИНАЯ СЕРВИСНАЯ ФУНКЦИЯ ОБРАБОТКИ ===
async def _process_call(
    message: RabbitMessage,
    broker: RabbitBroker,
    ari_manager: AriManager,
    session_factory: async_sessionmaker[AsyncSession],
    api_client: aiohttp.ClientSession,
    calls_locker: asyncio.Lock,
    concurrent_calls_semaphore: asyncio.Semaphore,
    fetch_iam_token: IamTokenFetcher,
    control_call_queue_gate: ControlCallQueueGate,
):
    body = json.loads(message.body)
    is_control = bool(body.get("is_control", False))
    routing_key = "call"

    if not ari_manager.is_connected:
        await broker.publish(
            body,
            exchange="calls",
            routing_key=routing_key,
            headers={"x-delay": CALL_RETRY_DELAYED_MESSAGE},
        )
        return

    phone_call_id = body.get("phone_call_id")
    injector = sa_inject_holder(session_factory)

    if await control_call_queue_gate.should_block_regular_calls(is_control=is_control):
        logger.info(
            "Control call is pending; re-queueing regular call %s until the control step completes",
            phone_call_id,
        )
        await broker.publish(
            body,
            exchange="calls",
            routing_key=routing_key,
            headers={"x-delay": CALL_RETRY_DELAYED_MESSAGE},
        )
        return

    # Если звонок контрольный — мы НЕ проверяем паузы и расписание внешних фильтров
    if not is_control:
        is_waiting = [
            is_wait_for_paused_calls(
                phone_call_id=phone_call_id,
                injector=injector,
                concurrent_calls_semaphore=concurrent_calls_semaphore,
            ),
            is_wait_for_next_retry(
                phone_call_id=phone_call_id,
                injector=injector,
                concurrent_calls_semaphore=concurrent_calls_semaphore,
            ),
            is_wait_for_ringing_calls(
                phone_call_id=phone_call_id,
                injector=injector,
                concurrent_calls_semaphore=concurrent_calls_semaphore,
            ),
            is_wait_for_call_schedule(
                phone_call_id=phone_call_id,
                ari_manager=ari_manager,
                injector=injector,
                concurrent_calls_semaphore=concurrent_calls_semaphore,
            ),
        ]
        is_waiting = await asyncio.gather(*is_waiting)
        if any(is_waiting):
            await broker.publish(
                body,
                exchange="calls",
                routing_key=routing_key,
                headers={"x-delay": CALL_RETRY_DELAYED_MESSAGE},
            )
            return

    async with calls_locker:
        await wait_for_busy_channels(ari_manager=ari_manager)

        async with injector() as pg_holder:
            call = await pg_holder.call_crud.get_by_phone_call_id(phone_call_id)

            if not call:
                phone_call = await pg_holder.phone_call_crud.get_by_id(phone_call_id)
                if phone_call:
                    logger.info(
                        "Control call row found directly by phone_call_id %s; continuing with direct processing",
                        phone_call_id,
                    )
                else:
                    logger.info(
                        "Call not found for processing queue with phone call id %s",
                        phone_call_id,
                    )
                    return

            id_channels = await get_active_id_channels(ari_manager=ari_manager)
            count_ringing = await pg_holder.phone_call_crud.get_count_ringing(
                id_channels=id_channels
            )

            # Для контрольного звонка игнорируем паузу (call.is_paused) и лимиты расписания channels
            if not is_control:
                if call.is_paused or not is_available_call_schedule(
                    schedule=call.schedule, count_ringing=count_ringing
                ):
                    await broker.publish(
                        body,
                        exchange="calls",
                        routing_key=routing_key,
                        headers={"x-delay": CALL_RETRY_DELAYED_MESSAGE},
                    )
                    return

            phone_call = await pg_holder.phone_call_crud.get_by_id(phone_call_id)
            if not phone_call:
                logger.info(
                    "Phone call id %s not found for processing queue",
                    phone_call_id,
                )
                return

            current_utc = datetime.utcnow()

            if not is_control and phone_call.next_retry_at and phone_call.next_retry_at > current_utc.replace(tzinfo=None):
                await broker.publish(
                    body,
                    exchange="calls",
                    routing_key=routing_key,
                    headers={"x-delay": CALL_RETRY_DELAYED_MESSAGE},
                )
                return

            try:
                await pg_holder.phone_call_crud.patch(
                    model=phone_call,
                    patch=PatchPhoneCall(
                        status="ringing",
                        next_retry_at=None,
                    ),
                )
                await pg_holder.commit()
            except IntegrityError:
                await pg_holder.rollback()
                await broker.publish(
                    body,
                    exchange="calls",
                    routing_key=routing_key,
                    headers={"x-delay": CALL_RETRY_DELAYED_MESSAGE},
                )
                return

            if not await is_stt_available(tts_type=call.tts_type):
                await pg_holder.phone_call_crud.patch(
                    model=phone_call,
                    patch=PatchPhoneCall(status="in_queue"),
                )
                await pg_holder.commit()
                await broker.publish(
                    body,
                    exchange="calls",
                    routing_key=routing_key,
                    headers={"x-delay": CALL_RETRY_DELAYED_MESSAGE},
                )
                return

            try:
                iam_token = await fetch_iam_token(api_client)
                # iam_token = "fake-test-iam-token"
                
                # Текст для контрольного звонка может быть статичным или браться из phone_call
                text_to_say = "Это контрольный звонок проверки доступности линии бэкенда." if is_control else phone_call.synthesis

                synthesized_speech, duration = await synthesize_speech(
                    tts_type=call.tts_type,
                    client=api_client,
                    iam_token=iam_token,
                    text=text_to_say,
                )

                await upload_audio_file(
                    client=api_client,
                    audio_bytes=synthesized_speech,
                    filename=phone_call.phone_number,
                )
            except RuntimeError as e:
                logger.warning(
                    "Failed to synthesize speech and upload audio file: %s", e
                )
                await pg_holder.phone_call_crud.patch(
                    model=phone_call,
                    patch=PatchPhoneCall(
                        status="failed",
                        cause="Не удалось выполнить синтез речи",
                        completed_at=current_utc.replace(tzinfo=None),
                    ),
                )
                await pg_holder.commit()
                return

            # Инициируем вызов через ARI Asterisk
            try:
                originate = await ari_manager.originate_call(
                    phone_number=phone_call.phone_number
                )
            except Exception as e:
                logger.warning(
                    "Failed to originate call for phone call id %s: %s", phone_call_id, e
                )
                await pg_holder.phone_call_crud.patch(
                    model=phone_call,
                    patch=PatchPhoneCall(
                        status="failed",
                        cause="Не удалось инициировать звонок через ARI Asterisk",
                        completed_at=current_utc.replace(tzinfo=None),
                    ),
                )
                await pg_holder.commit()
                return
            
            # Save ringing_at in UTC. Convert to local timezone only when rendering on UI.
            try:
                await pg_holder.phone_call_crud.patch(
                    model=phone_call,
                    patch=PatchPhoneCall(
                        ringing_at=current_utc.replace(tzinfo=None),
                        channel_id=originate.id,
                        duration=duration,
                    ),
                )
                await pg_holder.commit()
            except IntegrityError:
                logger.info(
                    "Patch phone call id %s failed, because channel id already exists (%s)",
                    phone_call_id,
                    originate.id,
                )
                await pg_holder.rollback()
                phone_call = await pg_holder.get_by_id(phone_call_id)
                await pg_holder.phone_call_crud.patch(
                    model=phone_call,
                    patch=PatchPhoneCall(
                        status="failed",
                        cause="Ошибка при обновлении канала телефонии",
                        completed_at=current_utc.replace(tzinfo=None),
                    ),
                )
                await pg_holder.commit()
                
        logger.info("ARI ORIGINATE RESULT: %s", getattr(originate, "id", None))
        return originate