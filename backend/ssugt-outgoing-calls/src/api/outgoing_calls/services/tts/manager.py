import asyncio
import re
import logging

import aiohttp
from typing import Optional, Tuple, Literal

from api.outgoing_calls.tools import extract_host_port
from api.outgoing_calls.services.tts.ssugt import (
    synthesize_speech as ssugt_synthesize_speech,
    SSUGT_TTS_URL,
)
from api.outgoing_calls.services.tts.edge import (
    synthesize_speech as edge_synthesize_speech,
    EDGE_TTS_URL,
)
from api.outgoing_calls.services.tts.tools import wrap_ssml, replace_pauses
from api.outgoing_calls.services.tts.yandex import (
    synthesize_speech as yandex_synthesize_speech,
    YANDEX_TTS_URL,
)

logger = logging.getLogger(__name__)

TTS_TYPE = Literal["ssugt", "yandex", "edge-tts"]

TTS_URL_MAP = {
    "ssugt": SSUGT_TTS_URL,
    "yandex": YANDEX_TTS_URL,
    "edge-tts": EDGE_TTS_URL,
}


async def is_stt_available(*, tts_type: TTS_TYPE, timeout: float = 2.0) -> bool:
    url = TTS_URL_MAP.get(tts_type, SSUGT_TTS_URL)

    host, port = extract_host_port(url=url)
    logger.info(
        f"DEBUG TTS CHECK: type={tts_type}, url={url} -> extracted host={host}, port={port}"
    )

    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()

        logger.info(f"DEBUG TTS CHECK: SUCCESS for {tts_type} ({host}:{port})")
        return True

    except asyncio.TimeoutError:
        logger.error(
            f"DEBUG TTS CHECK: TIMEOUT for {tts_type} ({host}:{port}) after {timeout}s"
        )
        return False
    except ConnectionRefusedError:
        logger.error(
            f"DEBUG TTS CHECK: CONNECTION REFUSED for {tts_type} ({host}:{port})"
        )
        return False
    except OSError as e:
        logger.error(f"DEBUG TTS CHECK: OS ERROR for {tts_type} ({host}:{port}): {e}")
        return False
    except Exception as e:
        logger.error(
            f"DEBUG TTS CHECK: UNKNOWN ERROR for {tts_type} ({host}:{port}): {type(e).__name__} - {e}"
        )
        return False


async def synthesize_speech(
    *,
    tts_type: TTS_TYPE,
    client: aiohttp.ClientSession,
    iam_token: str,
    text: str,
    lang: str = "ru-RU",
    voice: str = "",
    emotion: Optional[str] = "good",
) -> Tuple[bytes, float]:

    if tts_type == "ssugt":
        processed_text = replace_pauses(text)
        processed_text = wrap_ssml(processed_text)
        return await ssugt_synthesize_speech(
            client=client,
            iam_token=iam_token,
            text=processed_text,
            lang=lang,
            voice=voice or "kseniya",
            emotion=emotion,
        )

    if tts_type == "edge-tts":
        def replace_with_dots(match):
            ms = int(match.group(1))
            count = max(1, ms // 1000)
            return " ... " * count

        processed_text = re.sub(r'\[\s*пауза[:\s]+(\d+)\s*\]', replace_with_dots, text)
        
        result = await edge_synthesize_speech(
            client=client,
            iam_token=iam_token,
            text=processed_text,  
            lang=lang,
            voice=voice or "ru-RU-SvetlanaNeural",
            emotion=emotion or "neutral",
        )
        return result

    return await yandex_synthesize_speech(
        client=client,
        iam_token=iam_token,
        text=text,
        lang=lang,
        voice=voice or "alena",
        emotion=emotion,
    )
