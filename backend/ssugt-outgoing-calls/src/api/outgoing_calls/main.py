import asyncio
import logging
import os

import aiohttp
import uvicorn
from fastapi import FastAPI
from faststream import context
from faststream.rabbit import Channel, RabbitQueue
from faststream.rabbit.annotations import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession
from starlette.middleware.cors import CORSMiddleware

from api.outgoing_calls.database.postgres.tools import (
    sa_create_engine,
    sa_build_connection_uri,
    sa_create_session_factory,
    sa_create_holder,
)
from api.outgoing_calls.deps import (
    ApiClientMarker,
    DatabaseEngineMarker,
    DatabaseSessionFactoryMarker,
    DatabaseHolderMarker,
    IamTokenFetcherMarker,
    RabbitBrokerMarker,
)
from api.outgoing_calls.logger import LoggerGetFilter, handler as logger_handler, logger
from api.outgoing_calls.routes.amqp.calls import call_queue, calls_exchange, amqp_router
from api.outgoing_calls.routes.amqp.reports import reports_router
from api.outgoing_calls.services.ari.manager import AriManager
from api.outgoing_calls.routes.http.setup import register_http_router
from api.outgoing_calls.services.calls import fail_ringing_phone_calls
from api.outgoing_calls.services.control_call_queue import ControlCallQueueGate
from api.outgoing_calls.services.tts.yandex import make_iam_token_fetcher
from api.outgoing_calls.tools import build_amqp_url
from api.outgoing_calls.routes.http import auth, logs, users

RABBITMQ_CONSUMER_PREFETCH_COUNT = int(
    os.getenv("RABBITMQ_CONSUMER_PREFETCH_COUNT", "50")
)
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(LoggerGetFilter())
aioari_logger = logging.getLogger("aioari")
aioari_logger.setLevel(logging.INFO)
aioari_logger.addHandler(logger_handler)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


async def lifespan(app: FastAPI):
    engine: AsyncEngine = app.dependency_overrides[DatabaseEngineMarker]()  # type: ignore
    session_factory: async_sessionmaker[AsyncSession] = app.dependency_overrides[  # type: ignore
        DatabaseSessionFactoryMarker
    ]()

    broker = RabbitBroker(
        url=build_amqp_url(
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            port=int(os.getenv("RABBITMQ_PORT", 5672)),
            user=os.getenv("RABBITMQ_USER", "rabbitmq"),
            password=os.getenv("RABBITMQ_PASSWORD", "<PASSWORD>"),
        ),
        # logger=None,
        default_channel=Channel(prefetch_count=RABBITMQ_CONSUMER_PREFETCH_COUNT),
    )
    broker.include_router(amqp_router)
    broker.include_router(reports_router)

    calls_locker = asyncio.Lock()
    control_call_queue_gate = ControlCallQueueGate()

    concurrent_calls_semaphore = asyncio.Semaphore(
        int(os.getenv("MAX_PARALLEL_WAITING_CALLS", "10"))
    )

    fetch_iam_token = make_iam_token_fetcher()

    api_client = aiohttp.ClientSession()

    ari_manager = AriManager(
        api_client=api_client,
        pg_session_factory=session_factory,
        concurrent_calls_semaphore=concurrent_calls_semaphore,
        control_call_queue_gate=control_call_queue_gate,
        broker=broker,
        app_name=os.getenv("ARI_APP", default="myapp"),
        endpoint=os.getenv("ARI_ENDPOINT", default="3549838"),
        ari_url=os.getenv("ARI_URL", default="http://127.0.0.1:8088"),
        username=os.getenv("ARI_USERNAME", default="ariuser"),
        password=os.getenv("ARI_PASSWORD", default="<PASSWORD>"),
        caller_id=os.getenv("ARI_CALLER_ID", default="73833549838"),
    )

    context.set_global("broker", broker)
    context.set_global("ari_manager", ari_manager)
    context.set_global("session_factory", session_factory)
    context.set_global("api_client", api_client)
    context.set_global("calls_locker", calls_locker)
    context.set_global("control_call_queue_gate", control_call_queue_gate)
    context.set_global("concurrent_calls_semaphore", concurrent_calls_semaphore)
    context.set_global("fetch_iam_token", fetch_iam_token)

    app.dependency_overrides.update(  # type: ignore
        {
            ApiClientMarker: lambda: api_client,
            IamTokenFetcherMarker: lambda: fetch_iam_token,
            RabbitBrokerMarker: lambda: broker,
        }
    )


    ari_connected = False
    try:
        await ari_manager.connect()
        ari_connected = True
        logger.info("Successfully connected to Asterisk ARI")
    except Exception as e:
        logger.error(f"Skipping Asterisk ARI connection: {e}")
    
    # Мок для запуска ARI (в проде раскомментить строку выше)
    # ari_connected = False
    # try:
    #     ari_connected = True           # <-- ВСЁ РАВНО СТАВИМ TRUE ДЛЯ ТЕСТА
    #     logger.info("!!! [MOCK LIFESPAN] Фейковое успешное подключение к Asterisk ARI !!!")
    # except Exception as e:
    #     logger.error(f"Skipping Asterisk ARI connection: {e}")

    await broker.start()

    exchange = await broker.declare_exchange(calls_exchange)

    queue = await broker.declare_queue(call_queue)

    await queue.bind(exchange, routing_key="call")
    
    # === ДОБАВИТЬ: Декларация инфраструктуры для отчетов ===
    from faststream.rabbit import RabbitExchange
    
    reports_exchange = RabbitExchange("reports", durable=True)
    report_queue_obj = RabbitQueue("send_email", durable=True)
    
    declared_reports_exchange = await broker.declare_exchange(reports_exchange)
    declared_report_queue = await broker.declare_queue(report_queue_obj)
    await declared_report_queue.bind(declared_reports_exchange, routing_key="send_email")
    # ======================================================

    if ari_connected:
        asyncio.create_task(
            fail_ringing_phone_calls(
                ari_manager=ari_manager, session_factory=session_factory
            )
        )

    yield

    if ari_connected:
        try:
            await ari_manager.close()
        except Exception:
            pass
    await broker.stop()
    
    if not api_client.closed:
            await api_client.close()
            
    await engine.dispose()


def main() -> None:
    engine = sa_create_engine(
        connection_uri=sa_build_connection_uri(
            driver="asyncpg",
            host=os.getenv("POSTGRES_HOST", "pg"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "<PASSWORD>"),
            db=os.getenv("POSTGRES_DB", "postgres"),
        )
    )
    session_factory = sa_create_session_factory(engine=engine)

    app = FastAPI(lifespan=lifespan)  # type: ignore

    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(register_http_router())
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(logs.router, prefix="/logs", tags=["Logs"])

    app.dependency_overrides.update(  # noqa
        {
            DatabaseEngineMarker: lambda: engine,
            DatabaseSessionFactoryMarker: lambda: session_factory,
            DatabaseHolderMarker: sa_create_holder(session_factory=session_factory),
        }
    )

    uvicorn.run(
        app,
        host=os.getenv("OUTGOING_CALLS_SERVER_HOST", default="127.0.0.1"),
        port=int(os.getenv("OUTGOING_CALLS_SERVER_PORT", default="8191")),
    )


if __name__ == "__main__":
    main()
