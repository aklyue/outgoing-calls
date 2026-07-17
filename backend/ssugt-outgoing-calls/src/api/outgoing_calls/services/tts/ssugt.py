import os
from urllib.parse import urljoin

import aiohttp
from typing import Optional, Tuple

from api.outgoing_calls.logger import logger
from api.outgoing_calls.services.tts.tools import convert_to_wav

SSUGT_TTS_URL = urljoin(
    os.environ.get("TTS_SSUGT_BASE_URL", ""), "/speech/v1/tts:synthesize"
)


async def synthesize_speech(
    client: aiohttp.ClientSession,
    iam_token: str,
    text: str,
    lang: str = "ru-RU",
    voice: str = "xenia",
    emotion: Optional[str] = "good",
) -> Tuple[bytes, float]:
    headers = {"Authorization": f"Bearer {iam_token}"}

    data = {
        "text": text,
        "lang": lang,
        "voice": voice,
        "emotion": emotion,
        "format": "mp3",
        "sampleRateHertz": "48000",
    }

    async with client.post(SSUGT_TTS_URL, headers=headers, data=data) as response:
        if response.status != 200:
            error = await response.text()

            error_str = f"Ошибка синтеза: {response.status}, {error}"

            logger.error("Synthesize speech error %s for data %s", error_str, data)

            raise RuntimeError(error_str)

        wav_data = await response.read()
        wav_data, duration = await convert_to_wav(wav_data)
        return wav_data, duration
