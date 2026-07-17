import os

from urllib.parse import urljoin

import aiohttp

from api.outgoing_calls.logger import logger

STORAGE_SERVER_HOST = os.environ.get("STORAGE_CONTAINER_NAME", "storage")
STORAGE_SERVER_PORT = int(os.environ.get("STORAGE_SERVER_PORT", "8190"))
BASE_URL = f"http://{STORAGE_SERVER_HOST}:{STORAGE_SERVER_PORT}/"

UPLOAD_URL = urljoin(BASE_URL, "upload/")
DELETE_URL = urljoin(BASE_URL, "delete/")


async def upload_audio_file(
    *,
    client: aiohttp.ClientSession,
    audio_bytes: bytes,
    filename: str,
) -> dict:
    data = aiohttp.FormData()
    data.add_field(
        "file", audio_bytes, filename=f"{filename}.wav", content_type="audio/wav"
    )
    data.add_field("filename", filename)

    async with client.post(UPLOAD_URL, data=data) as response:
        if response.status != 200:
            error = await response.text()

            error_str = f"Ошибка загрузки: {response.status}, {error}"

            logger.error("Upload audio file error: %s", error_str)

            raise RuntimeError(error_str)

        return await response.json()


async def delete_audio_file(
    *,
    client: aiohttp.ClientSession,
    filename: str,
) -> dict:
    url = urljoin(DELETE_URL, filename)
    async with client.delete(url) as response:
        if response.status != 200:
            error = await response.text()

            error_str = f"Ошибка удаления: {response.status}, {error}"

            logger.error("Delete audio file error: %s", error_str)

            raise RuntimeError(error_str)

        return await response.json()
