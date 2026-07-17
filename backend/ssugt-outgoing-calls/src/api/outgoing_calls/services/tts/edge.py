import os
import re
import struct
from urllib.parse import urljoin
import aiohttp
from typing import Optional, Tuple
import asyncio

from api.outgoing_calls.logger import logger
from api.outgoing_calls.services.tts.tools import convert_to_wav

EDGE_TTS_URL = urljoin(
    os.environ.get("TTS_EDGE_BASE_URL", "http://127.0.0.1:8195"),
    "/speech/v1/tts:synthesize",
)


def generate_pcm_silence(duration_ms: int, sample_rate: int = 48000) -> bytes:
    """Генерирует PCM байты тишины для 16-bit Mono (2 байта на семпл)."""
    num_samples = int((sample_rate * duration_ms) / 1000)
    return b"\x00" * (num_samples * 2)


async def request_single_phrase(client: aiohttp.ClientSession, data: dict, max_retries: int = 3) -> bytes:
    """Запрашивает синтез фразы у микросервиса с 3 попытками в случае сбоя сети Microsoft."""
    for attempt in range(max_retries):
        try:
            async with client.post(EDGE_TTS_URL, json=data) as response:
                if response.status == 200:
                    wav_data = await response.read()
                    if wav_data.startswith(b"RIFF"):
                        data_start = wav_data.find(b"data")
                        if data_start != -1:
                            return wav_data[data_start + 8:]
                    return wav_data
                
                # Если микросервис вернул 500 (сеть Майкрософта упала), мы не падаем сразу
                error = await response.text()
                logger.warning(f"Попытка {attempt + 1} неуспешна: статус {response.status}, ошибка: {error}")
        
        except Exception as e:
            logger.warning(f"Попытка {attempt + 1} упала по исключению: {e}")
        
        # Ждем чуть-чуть перед следующей попыткой (0.5 сек, 1 сек, 1.5 сек)
        await asyncio.sleep(0.5 * (attempt + 1))
        
    raise RuntimeError("Microsoft Edge TTS полностью заблокировал запросы после 3 попыток.")


def build_final_wav(combined_pcm: bytes, sample_rate: int = 48000) -> bytes:
    """Собирает эталонный WAV-заголовок вокруг склеенных PCM данных."""
    channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * channels * (bits_per_sample // 8)
    block_align = channels * (bits_per_sample // 8)

    data_size = len(combined_pcm)
    riff_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        riff_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + combined_pcm


async def synthesize_speech(
    client: aiohttp.ClientSession,
    iam_token: str,
    text: str,
    lang: str = "ru-RU",
    voice: str = "ru-RU-SvetlanaNeural",
    emotion: Optional[str] = "neutral",
    speed: float = 1.0,
) -> Tuple[bytes, float]:

    # Режем входящий текст по маркеру [пауза 1000]
    parts = re.split(r"\[\s*пауза[:\s]+(\d+)\s*\]", text)

    combined_pcm = b""

    for i, part in enumerate(parts):
        if not part:
            continue

        if i % 2 == 1:
            # Добавляем честную PCM тишину заданной длины
            duration_ms = int(part)
            combined_pcm += generate_pcm_silence(duration_ms)
        else:
            phrase_text = part.strip()
            if phrase_text:
                data = {
                    "text": phrase_text,
                    "lang": lang,
                    "voice": voice,
                    "emotion": emotion,
                    "speed": speed,
                    "format": "wav",
                    "sampleRateHertz": 48000,
                }
                phrase_pcm = await request_single_phrase(client, data)
                combined_pcm += phrase_pcm

    if not combined_pcm:
        raise RuntimeError("No audio data generated")

    # Собираем валидный WAV-файл из склеенных PCM данных
    final_wav = build_final_wav(combined_pcm, sample_rate=48000)

    # Прогоняем через вашу внутреннюю утилиту для расчета duration
    final_wav, duration = await convert_to_wav(final_wav)
    return final_wav, duration
