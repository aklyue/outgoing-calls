import asyncio
import json
import logging

from aioari.client import Client
from aiohttp import WSMsgType
from aioswagger11.http_client import AsynchronousHttpClient, ApiKeyAuthenticator
import urllib.parse

logger = logging.getLogger(__name__)


class SafeHttpClient(AsynchronousHttpClient):

    async def ws_connect(self, url, params=None):
        if self.authenticator is not None and self.authenticator.matches(url):
            if params is None:
                params = {}
            self.authenticator.apply(params, params)

        if params:
            joined_params = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{joined_params}"

        ret = await self.session.ws_connect(
            url,
            heartbeat=30,  # каждые 30 секунд ping/pong
            timeout=30,  # общий таймаут на подключение
            # receive_timeout=60,  # если 60 секунд нет сообщений — закрыть
            autoping=True,
        )

        self.websockets.add(ret)
        return ret


class SafeClient(Client):

    def __init__(self, base_url, http_client, *, event_idle_timeout=1800):
        super().__init__(base_url, http_client)
        self._event_idle_timeout = event_idle_timeout

    async def _drain_ws(self, ws):
        while True:
            try:
                msg = await asyncio.wait_for(
                    ws.receive(), timeout=self._event_idle_timeout
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "No ARI events for %s seconds: closing websocket",
                    self._event_idle_timeout,
                )
                return

            if msg is None:
                return
            if msg.type in {WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING}:
                logger.warning("ARI websocket connection is closing")

                return
            if msg.type == WSMsgType.ERROR:
                raise ws.exception()

            if msg.type != WSMsgType.TEXT:
                continue

            try:
                payload = json.loads(msg.data)
            except Exception:
                logger.exception("Invalid JSON from ARI: %r", msg.data)
                continue

            if not isinstance(payload, dict) or "type" not in payload:
                logger.error("Invalid ARI event: %r", payload)
                continue

            # logger.info("Processed ARI event: %r", payload.get("type"))

            await self.process_ws(payload)

    async def run(self, apps, *, _test_msgs=None):
        if _test_msgs is None:
            _test_msgs = []
        if isinstance(apps, list):
            apps = ",".join(apps)

        ws = await self.swagger.events.eventWebsocket(app=apps)
        self.websockets.add(ws)

        for m in _test_msgs:
            ws.push(m)

        try:
            await self._drain_ws(ws)
        finally:
            await ws.close()
            self.websockets.remove(ws)


async def ari_safe_connect(base_url, username, password, loop=None):
    host = urllib.parse.urlparse(base_url).hostname
    http_client = SafeHttpClient(
        loop=loop, auth=ApiKeyAuthenticator(host, f"{username}:{password}")
    )
    client = SafeClient(base_url, http_client)
    await client.init()
    return client
