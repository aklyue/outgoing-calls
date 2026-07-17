import asyncio
import os
from asyncio import Task
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List, Callable, Awaitable
from api.outgoing_calls.database.postgres.crud.phone_call import PhoneCall

import aioari
import aiohttp
from aioari.model import Channel
from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from api.outgoing_calls.services.ari.client import ari_safe_connect
from api.outgoing_calls.database.postgres.crud.phone_call import PatchPhoneCall
from api.outgoing_calls.database.postgres.tools import sa_inject_holder
from api.outgoing_calls.services.control_call_queue import ControlCallQueueGate
from api.outgoing_calls.services.storage import delete_audio_file
from api.outgoing_calls.logger import logger

NO_RESPONDED_CALL_RETRY_IN_SECONDS = int(
    os.getenv("NO_RESPONDED_CALL_RETRY_IN_SECONDS", "30")
)
CAUSE_CODE_MAP = {
    0: "Нет ответа от абонента",
    1: "Номер не назначен (не существует)",
    2: "Нет маршрута к указанной транзитной сети",
    3: "Нет маршрута к месту назначения",
    6: "Канал неприемлем",
    7: "Вызов уже устанавливается по существующему каналу",
    16: "Вызов завершен",
    17: "Абонент занят",
    18: "Абонент не отвечает",
    19: "Нет ответа от абонента",
    20: "Абонент отсутствует",
    21: "Вызов отклонен",
    22: "Номер изменен",
    23: "Перенаправление на новый номер",
    25: "Ошибка маршрутизации на станции",
    27: "Назначение неисправно или недоступно",
    28: "Неверный формат номера",
    29: "Услуга отклонена",
    30: "Ответ на запрос статуса",
    31: "Абонент повесил трубку",
    34: "Нет доступного канала/транка",
    38: "Сеть недоступна (вышла из строя)",
    41: "Временный сбой",
    42: "Перегрузка оборудования коммутации",
    43: "Информация доступа отброшена",
    44: "Запрашиваемый канал недоступен",
    47: "Недоступность ресурсов (неуточненная)",
    50: "Нет подписки на запрашиваемую услугу",
    52: "Исходящие вызовы запрещены",
    54: "Входящие вызовы запрещены",
    57: "Возможность передачи не разрешена",
    58: "Возможность передачи недоступна",
    63: "Услуга или опция недоступна (неуточненно)",
    65: "Возможность передачи не реализована",
    66: "Тип канала не реализован",
    69: "Запрашиваемая функция не реализована",
    70: "Доступна только ограниченная цифровая передача",
    79: "Услуга или опция не реализована (неуточненно)",
    81: "Недопустимое значение ссылки на вызов",
    88: "Несовместимое назначение",
    95: "Недопустимое сообщение (неуточненное)",
    96: "Отсутствует обязательный информационный элемент",
    97: "Неизвестный или не реализованный тип сообщения",
    98: "Сообщение не совместимо с текущим состоянием вызова",
    99: "Неизвестный или не реализованный параметр",
    100: "Неверное содержимое информационного элемента",
    101: "Сообщение не совместимо с состоянием вызова",
    102: "Таймаут ожидания (восстановление по таймеру)",
    111: "Протокольная ошибка (неуточненная)",
    127: "Ошибка взаимодействия между сетями (неуточненная)",
}
IGNORED_CAUSE_CODES = [
    16,  # Normal call clearing — абонент завершил вызов
    # 17,  # User busy — абонент занят (не ошибка, а ожидаемая ситуация)
    18,  # No user responding — абонент не ответил
    19,  # No answer from user — прозвонили, но не ответили
    # 20,  # Subscriber absent — абонент временно недоступен
    21,  # Call rejected — абонент/система отклонил(а) вызов
    22,  # Number changed — номер изменен
    486,  # Busy Here — иногда проксируется как SIP-код в Asterisk
]
NO_RESPONDED_CAUSE_CODES = [
    0,  # Unknown — причина не определена
    17,  # User busy — абонент занят (не ответил из-за занятости линии)
    18,  # No user responding — абонент не ответил (нет реакции)
    19,  # No answer from user — прозвонили, но не ответили
    20,  # Subscriber absent — абонент временно недоступен
]
ConnectionCallbackType = Callable[[Any], Awaitable[None]]


def get_cause_description(cause_code: Optional[int]):
    return CAUSE_CODE_MAP.get(cause_code, "Неизвестная причина")


class AriManager:

    def __init__(
        self,
        *,
        api_client: aiohttp.ClientSession,
        pg_session_factory: async_sessionmaker[AsyncSession],
        concurrent_calls_semaphore: asyncio.Semaphore,
        control_call_queue_gate: ControlCallQueueGate,
        broker: RabbitBroker,
        app_name: str,
        endpoint: str,
        ari_url: str,
        username: str,
        password: str,
        caller_id: str,
    ) -> None:
        self._api_client = api_client
        self._pg_session_factory = pg_session_factory
        self._concurrent_calls_semaphore = concurrent_calls_semaphore
        self._control_call_queue_gate = control_call_queue_gate
        self._broker = broker
        self._app_name = app_name
        self._endpoint = endpoint
        self._ari_url = ari_url
        self._username = username
        self._password = password
        self._caller_id = caller_id
        self._client: Optional[aioari.Client] = None
        self._reconnector_running = False
        self._runner_task: Optional[Task] = None

    @property
    def is_connected(self) -> bool:
        return self._client and len(self._client.websockets) > 0
        # return True  # <-- ТЕСТОВАЯ ЗАГЛУШКА: всегда подключены

    async def connect(self) -> None:
        self._client = await ari_safe_connect(
            base_url=self._ari_url, username=self._username, password=self._password
        )

        self._client.on_event("ApplicationReplaced", self._application_replaced)
        self._client.on_channel_event(
            "ChannelStateChange", self._on_channel_state_change
        )
        self._client.on_event("PlaybackFinished", self._on_playback_finished)
        self._client.on_channel_event("ChannelDestroyed", self._on_channel_destroyed)

        self._reconnector_running = True

        self._runner_task = asyncio.create_task(self._runner())

    async def _runner(self) -> None:
        logger.info("Connecting to websocket ARI with app %r", self._app_name)

        while self._reconnector_running:
            try:
                await self._client.run(apps=self._app_name)
            except Exception as e:
                logger.warning("ARI websocket disconnected or failed: %s", e)
            finally:
                logger.info("Reconnecting to websocket ARI with app %r", self._app_name)

    async def close(self) -> None:
        self._reconnector_running = False

        if self._runner_task:
            self._runner_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._runner_task

        await self._client.close()

    async def active_channels(self) -> List[Channel]:

        # logger.info("!!! [MOCK ARI] active_channels возвращает пустой список !!!")
        # return []

        channels = await self._client.channels.list()

        channels = [
            channel
            for channel in channels
            if channel.json.get("name", "").startswith(f"PJSIP/{self._endpoint}")
            or (f"@{self._endpoint}" in channel.json.get("name", ""))
        ]

        return channels

    async def hangup(self, channel_id: str) -> None:
        try:
            channel = await self._client.channels.get(channelId=channel_id)

            if not channel:
                return

            await channel.hangup()
        except Exception as e:
            pass

    async def _application_replaced(self, event: Dict[str, Any]) -> None:
        logger.info("On application replaced event: %s", event)

    async def _on_playback_finished(self, event: Dict[str, Any]) -> None:
        playback = event["playback"]
        target: str = playback["target_uri"]

        if not target.startswith("channel:"):
            logger.error(
                "On playback finished, skipping playback finished event: %s", event
            )

            return

        channel_id = target.split(":")[1]

        try:
            channel = await self._client.channels.get(channelId=channel_id)  # type: ignore[union-attr]

            await asyncio.sleep(1)

            await channel.hangup()

            injector = sa_inject_holder(self._pg_session_factory)

            async with self._concurrent_calls_semaphore:
                async with injector() as pg_holder:
                    phone_call = await pg_holder.phone_call_crud.get_by_channel_id(
                        channel.id
                    )

                    if not phone_call:
                        return

                    logger.info("On playback finished: %s", phone_call.phone_number)
        except Exception as e:
            pass

    async def _on_channel_state_change(
        self, channel: Channel, event: Dict[str, Any]
    ) -> None:
        if channel.json["state"] != "Up":
            return

        await asyncio.sleep(0.5)

        injector = sa_inject_holder(self._pg_session_factory)

        async with self._concurrent_calls_semaphore:
            async with injector() as pg_holder:
                phone_call = await pg_holder.phone_call_crud.get_by_channel_id(
                    channel.id
                )

                if not phone_call:
                    logger.error(
                        f"CRITICAL: Phone call not found for channel_id={channel.id}"
                    )
                    return

                media = f"sound:custom/{phone_call.phone_number}"

                logger.info(
                    "On channel state change for phone number %s, play audio: %s",
                    phone_call.phone_number,
                    media,
                )

                try:
                    await channel.play(media=media)
                except Exception as e:
                    logger.warning("On channel state change play failed: %s", e)
                else:
                    await pg_holder.phone_call_crud.patch(
                        model=phone_call,
                        patch=PatchPhoneCall(
                            picked_up_at=datetime.utcnow().replace(tzinfo=None)
                        ),
                    )
                    await pg_holder.commit()

    async def _on_channel_destroyed(
        self, channel: Channel, event: Dict[str, Any]
    ) -> None:
        logger.info(
            "[CHANNEL_DESTROYED ENTER] channel_id=%s event=%s", channel.id, event
        )
        injector = sa_inject_holder(self._pg_session_factory)

        async with self._concurrent_calls_semaphore:
            async with injector() as pg_holder:
                phone_call = await pg_holder.phone_call_crud.get_by_channel_id(
                    channel.id
                )

                logger.info(
                    "[DB LOOKUP] channel_id=%s found=%s phone_call_id=%s phone=%s",
                    channel.id,
                    bool(phone_call),
                    getattr(phone_call, "id", None),
                    getattr(phone_call, "phone_number", None),
                )

                if not phone_call:
                    return

                logger.info(
                    "On channel destroyed, delete audio file for phone number: %s",
                    phone_call.phone_number,
                )

                # try:
                #     await delete_audio_file(
                #         client=self._api_client, filename=phone_call.phone_number
                #     )
                # except RuntimeError:
                #     logger.warning(
                #         "Could not delete audio file for phone number: %s",
                #         phone_call.phone_number,
                #     )

                cause = event.get("cause")
                code = int(cause) if cause is not None else None

                logger.info(
                    "[CAUSE RAW] channel_id=%s cause=%s type=%s",
                    channel.id,
                    cause,
                    type(cause),
                )

                cause = event.get("cause")
                logger.info("DEBUG: Call finished. Cause code received: %s", cause)

                if code == 16:
                    status = "done"
                elif code in NO_RESPONDED_CAUSE_CODES:
                    status = "no_answer"
                else:
                    status = "failed"

                logger.info(
                    "[STATUS CALC] channel_id=%s code=%s status=%s ignored=%s",
                    channel.id,
                    code,
                    status,
                    code in IGNORED_CAUSE_CODES if code is not None else None,
                )

                retry_count = phone_call.retry_count + 1
                current_utc = datetime.utcnow()

                phone_call_patch = PatchPhoneCall(
                    completed_at=current_utc.replace(tzinfo=None),
                    status=status,
                    code=code,
                    cause=get_cause_description(cause),
                    retry_count=retry_count,
                )
                is_need_retry_call = False

                call = await pg_holder.call_crud.get_by_phone_call_id(phone_call.id)

                if code is not None and code in NO_RESPONDED_CAUSE_CODES:
                    if call and call.retry_limit > retry_count:
                        next_retry_at = current_utc + timedelta(
                            minutes=NO_RESPONDED_CALL_RETRY_IN_SECONDS / 60
                        )

                        logger.info(
                            "Retry call for phone %s with next retry at %s",
                            phone_call.phone_number,
                            str(next_retry_at),
                        )

                        phone_call_patch = PatchPhoneCall(
                            ringing_at=None,
                            status="in_queue",
                            retry_count=retry_count,
                            next_retry_at=next_retry_at.replace(tzinfo=None),
                        )
                        is_need_retry_call = True

                logger.info(
                    "[DB PATCH BEFORE] phone_call_id=%s retry_count=%s status=%s next_retry=%s",
                    phone_call.id,
                    retry_count,
                    phone_call_patch["status"],
                    getattr(phone_call_patch, "next_retry_at", None),
                )

                await pg_holder.phone_call_crud.patch(
                    model=phone_call, patch=phone_call_patch
                )

                await pg_holder.commit()

                logger.info(
                    "[DB PATCH AFTER] phone_call_id=%s committed", phone_call.id
                )

                is_control_call = bool(status == "done" and phone_call.is_control)

                if is_control_call:

                    logger.info(
                        "[CONTROL CHECK] call_id=%s is_control_call=%s phone=%s control=%s",
                        call.id if call else None,
                        is_control_call,
                        phone_call.phone_number,
                        getattr(call, "control_call_number", None) if call else None,
                    )

                    await self._control_call_queue_gate.finish_control_call(
                        phone_call_id=str(phone_call.id)
                    )

                    await pg_holder.commit()

                # === EMAIL REPORT TRIGGERS (for ANY completed call, not just control calls) ===
                if call and status == "done":
                    # Interval trigger
                    if (
                        call.email_report_enabled
                        and call.email_report_trigger_interval
                        and call.email_report_address
                    ):
                        call.current_email_report_counter += 1
                        if (
                            call.current_email_report_counter
                            >= call.email_report_interval
                        ):
                            call.current_email_report_counter = 0

                            await self._broker.publish(
                                {
                                    "call_id": call.id,
                                    "email": call.email_report_address,
                                    "trigger": "interval",
                                },
                                exchange="reports",
                                routing_key="send_email",
                            )

                    # Final trigger
                    if (
                        call.email_report_enabled
                        and call.email_report_trigger_final
                        and call.email_report_address
                    ):
                        remaining_calls = (
                            await pg_holder.phone_call_crud.get_count_active_by_call_id(
                                call.id
                            )
                        )
                        if remaining_calls == 0:
                            await self._broker.publish(
                                {
                                    "call_id": call.id,
                                    "email": call.email_report_address,
                                    "trigger": "final",
                                },
                                exchange="reports",
                                routing_key="send_email",
                            )

                    await pg_holder.commit()

                if call and status == "done" and not is_control_call:
                    if call.control_call_enabled and call.control_call_number:
                        pending_control_count = await pg_holder.phone_call_crud.get_count_pending_control_calls(
                            call.id
                        )
                        if pending_control_count > 0:
                            logger.info(
                                "Skipping dynamic control_call publish because %s pending control calls exist for call %s",
                                pending_control_count,
                                call.id,
                            )
                        else:
                            call.current_control_call_counter += 1
                            logger.info(
                                "Control call counter for call %s: %s/%s",
                                call.id,
                                call.current_control_call_counter,
                                call.control_call_interval,
                            )
                            if (
                                call.current_control_call_counter
                                >= call.control_call_interval
                            ):
                                call.current_control_call_counter = 0
                                logger.info(
                                    "DEBUG: Trying to publish control_call to broker"
                                )

                                new_model = PhoneCall(
                                    call_id=call.id,
                                    phone_number=call.control_call_number,
                                    synthesis="[CONTROL] Контрольный звонок. Проверка работоспособности каналов связи.",
                                    status="in_queue",
                                    created_at=current_utc.replace(tzinfo=None),
                                    is_control=True,
                                )
                                new_control_phone_call = (
                                    await pg_holder.phone_call_crud.create(new_model)
                                )
                                await pg_holder.commit()
                                await self._control_call_queue_gate.begin_control_call(
                                    phone_call_id=str(new_control_phone_call.id)
                                )

                                await self._broker.publish(
                                    {
                                        "phone_call_id": new_control_phone_call.id,
                                        "is_control": True,
                                    },
                                    exchange="calls",
                                    routing_key="call",
                                    headers={"x-delay": 3000},
                                )
                                logger.info("DEBUG: Successfully published control_call")

                if is_need_retry_call:
                    await self._broker.publish(
                        {"phone_call_id": phone_call.id},
                        exchange="calls",
                        routing_key="call",
                        headers={"x-delay": NO_RESPONDED_CALL_RETRY_IN_SECONDS},
                    )

    async def originate_call(self, *, phone_number: str) -> Channel:
        # Теперь семафор реально ограничивает количество исходящих запросов
        async with self._concurrent_calls_semaphore:
            logger.info("Originate call on phone number %s", phone_number)

            logger.info(
                "[TRACE ORIGINATE] phone=%s app=%s endpoint=%s",
                phone_number,
                self._app_name,
                self._endpoint,
            )

            logger.info(
                "[TRACE INVITE OUT] phone=%s endpoint=%s concurrent_before=%s",
                phone_number,
                self._endpoint,
                self._concurrent_calls_semaphore._value,
            )

            originate = await self._client.channels.originate(
                endpoint=f"PJSIP/{phone_number}@{self._endpoint}",
                app=self._app_name,
                callerId=self._caller_id,
            )

            logger.info(
                "[TRACE INVITE RAW RESULT] phone=%s channel=%s state=%s json=%s",
                phone_number,
                originate.id,
                originate.json.get("state"),
                originate.json,
            )

            return originate

    # # Мок версия функции
    # async def originate_call(self, *, phone_number: str) -> Any:
    #     logger.info("!!! [MOCK ARI] Эмуляция вызова на номер %s !!!", phone_number)

    #     # Создаем фейковый объект, имитирующий объект Channel из aioari
    #     class MockChannel:
    #         id = "mock-channel-id-12345"

    #     # Даем коду чуть-чуть «подышать» асинхронно
    #     await asyncio.sleep(0.1)

    #     return MockChannel()
