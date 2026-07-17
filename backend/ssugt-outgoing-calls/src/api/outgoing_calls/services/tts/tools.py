import asyncio
import os
import re
import subprocess
import tempfile
from typing import Tuple

from api.outgoing_calls.logger import logger


def is_ssml(text: str) -> bool:
    return bool(re.search(r"<\w+", text))


def wrap_ssml(text: str) -> str:
    if is_ssml(text):
        if not text.startswith("<speak>"):
            text = "<speak>" + text
        if not text.endswith("</speak>"):
            text = text + "</speak>"

    return text


def replace_pauses(text: str) -> str:
    return re.sub(
        r"\[\s*пауза\s*(\d+)\s*\]",
        lambda m: f'<break time="{m.group(1)}ms"/>',
        text,
        flags=re.IGNORECASE,
    )


async def convert_to_wav(audio_data: bytes) -> Tuple[bytes, float]:

    def _convert_to_wav(audio_data: bytes) -> Tuple[bytes, float]:  # type: ignore
        with tempfile.NamedTemporaryFile(delete=False, suffix=".audio") as audio_file:
            audio_file.write(audio_data)
            audio_path = audio_file.name

        wav_path = audio_path.replace(".audio", ".wav")
        wav_data = bytes()
        duration = 0.0

        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    audio_path,
                    "-ar",
                    "8000",
                    "-ac",
                    "1",
                    "-f",
                    "wav",
                    wav_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if result.returncode != 0 or not os.path.exists(wav_path):
                raise RuntimeError("Ошибка при конвертации MP3 в WAV")

            with open(wav_path, "rb") as wav_file:
                wav_data = wav_file.read()

            duration_info = subprocess.run(
                ["ffmpeg", "-i", wav_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )

            match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", duration_info.stderr)
            if match:
                hours, minutes, seconds = match.groups()
                duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)

            return wav_data, duration
        except Exception as e:
            logger.error("Error converting MP3 file to WAV: %s", e)
            return wav_data, duration
        finally:
            for path in (audio_path, wav_path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    return await asyncio.to_thread(_convert_to_wav, audio_data)
