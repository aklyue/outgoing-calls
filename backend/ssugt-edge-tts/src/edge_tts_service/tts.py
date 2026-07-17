import io
import logging
import os
import re
import struct
import edge_tts

logger = logging.getLogger(__name__)

DEFAULT_VOICE = os.getenv("EDGE_TTS_DEFAULT_VOICE", "ru-RU-SvetlanaNeural")
DEFAULT_RATE = os.getenv("EDGE_TTS_DEFAULT_RATE", "+0%")
DEFAULT_VOLUME = os.getenv("EDGE_TTS_DEFAULT_VOLUME", "+0%")
DEFAULT_PITCH = os.getenv("EDGE_TTS_DEFAULT_PITCH", "+0Hz")

SUPPORTED_VOICES = [
    "ru-RU-DariyaNeural",
    "ru-RU-SvetlanaNeural",
    "ru-RU-DmitryNeural",
    "ru-RU-MarinaNeural",
]

VOICE_ALIASES = {
    "baya": "ru-RU-SvetlanaNeural",
    "aidar": "ru-RU-DmitryNeural",
    "kseniya": "ru-RU-DariyaNeural",
    "xenia": "ru-RU-DariyaNeural",
    "eugene": "ru-RU-DmitryNeural",
    "dariya": "ru-RU-DariyaNeural",
    "svetlana": "ru-RU-SvetlanaNeural",
    "dmitry": "ru-RU-DmitryNeural",
    "marina": "ru-RU-MarinaNeural",
}


def resolve_voice(voice: str) -> str:
    if voice in VOICE_ALIASES:
        return VOICE_ALIASES[voice]
    if voice in SUPPORTED_VOICES:
        return voice
    return voice


def generate_wav_silence(duration_ms: int, sample_rate: int = 48000) -> bytes:
    """Генерирует чистые байты тишины для 16-bit Mono PCM (2 байта на семпл)."""
    num_samples = int((sample_rate * duration_ms) / 1000)
    return b"\x00" * (num_samples * 2)


async def synthesize_phrase(text: str, voice: str, rate: str) -> bytes:
    """Синтезирует отдельную фразу через стандартный метод библиотеки."""
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


def combine_wav_files(wav_chunks: list[bytes]) -> bytes:
    """
    Принимает список полноценных WAV/MP3 файлов или кусков данных.
    Если edge-tts отдал медиа-контейнер, мы объединяем аудио-данные,
    пропуская заголовки, если они присутствуют.
    """
    combined_data = b""
    
    for chunk in wav_chunks:
        if not chunk:
            continue
        # Если это кусок тишины, который мы сгенерировали сами, в нем нет RIFF заголовка
        if chunk.startswith(b"RIFF"):
            try:
                # Ищем подстроку 'data' в заголовке WAV, чтобы вытащить сырые PCM-байты
                data_start = chunk.find(b"data")
                if data_start != -1:
                    # Пропускаем 4 байта слова 'data' и 4 байта размера данных
                    raw_audio = chunk[data_start + 8:]
                    combined_data += raw_audio
                else:
                    combined_data += chunk
            except Exception:
                combined_data += chunk
        else:
            # Если это уже сырые байты тишины
            combined_data += chunk

    if not combined_data:
        return b""

    # Собираем эталонный каноничный заголовок WAV (RIFF) для 48000Hz, 16-bit, Mono
    sample_rate = 48000
    channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * channels * (bits_per_sample // 8)
    block_align = channels * (bits_per_sample // 8)
    
    data_size = len(combined_data)
    riff_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", riff_size, b"WAVE",
        b"fmt ", 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample,
        b"data", data_size
    )
    
    return header + combined_data


async def synthesize(
    text: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    volume: str = DEFAULT_VOLUME,
    pitch: str = DEFAULT_PITCH,
) -> bytes:
    voice_name = resolve_voice(voice)
    clean_text = text.strip()

    # Больше никакого геморроя с SSML и байтами. Работает только стандартный stream()
    communicate = edge_tts.Communicate(
        text=clean_text,
        voice=voice_name,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    
    audio_chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    if not audio_chunks:
        raise RuntimeError("Empty audio result from edge-tts")

    return b"".join(audio_chunks)
