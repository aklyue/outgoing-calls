import io
import logging
import os
import re
import asyncio
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, Form, Response, HTTPException, Depends, APIRouter
import soundfile as sf
from functools import lru_cache

from synthesizer.logger import setup_logging
from synthesizer.normalizer import preprocess_text, split_text

logger = logging.getLogger(__name__)
router = APIRouter()


@dataclass
class TTSConfig:
    device: str
    speakers: List[str]
    sample_rate: int
    model: Optional[torch.nn.Module] = None


@lru_cache(maxsize=1)
def get_config() -> TTSConfig:
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    speakers: List[str] = ["aidar", "baya", "kseniya", "xenia", "eugene"]
    sample_rate: int = int(os.getenv("SYNTHESIZER_SAMPLE_RATE", "48000"))
    return TTSConfig(device=device, speakers=speakers, sample_rate=sample_rate)


def load_tts_model(config: TTSConfig) -> None:
    if config.model:
        return

    m, _ = torch.hub.load(
        repo_or_dir="snakers4/silero-models",
        model="silero_tts",
        language="ru",
        speaker="v3_1_ru",
        verbose=False,
        trust_repo=True,
    )

    to_fn = getattr(m, "to", None)
    if callable(to_fn):
        to_fn(config.device)

    config.model = m

    logger.info(
        "Synthesizer STT model loaded %r with device %r",
        type(config.model),
        config.device,
    )


async def ensure_model_loaded(config: TTSConfig) -> None:
    if config.model:
        return

    await asyncio.to_thread(load_tts_model, config)


async def lifespan(app: FastAPI):
    cfg = get_config()
    await ensure_model_loaded(cfg)
    yield


def synthesize(config: TTSConfig, text: str, speaker: str, sample_rate: int) -> bytes:
    wavs: List[np.ndarray] = []
    text = preprocess_text(text)

    assert config.model is not None, "TTS model is not loaded"

    with torch.inference_mode():
        text = preprocess_text(text)

        if re.search(r"<\w+", text):
            text = text.strip()
            if not text.startswith("<speak>"):
                text = "<speak>" + text
            if not text.endswith("</speak>"):
                text = text + "</speak>"

            audio = config.model.apply_tts(
                ssml_text=text,
                speaker=speaker,
                sample_rate=sample_rate,
                put_accent=True,
                put_yo=True,
            )
            arr = audio.detach().cpu().numpy().astype(np.float32)
            wavs.append(arr)
        else:
            chunks = split_text(text, max_len=500)
            for chunk in chunks:
                audio = config.model.apply_tts(
                    text=chunk,
                    speaker=speaker,
                    sample_rate=sample_rate,
                    put_accent=True,
                    put_yo=True,
                )
                if isinstance(audio, torch.Tensor):
                    arr = audio.detach().cpu().numpy().astype(np.float32)
                else:
                    arr = np.array(audio, dtype=np.float32)
                wavs.append(arr)

    if not wavs:
        raise RuntimeError("Empty audio result")

    audio_cat: np.ndarray = np.concatenate(wavs)
    buf: io.BytesIO = io.BytesIO()
    sf.write(buf, audio_cat, sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@router.post("/speech/v1/tts:synthesize")
async def do_synthesize(
    text: str = Form(...),
    lang: str = Form("ru-RU"),
    voice: str = Form("baya"),
    emotion: str = Form("neutral"),
    speed: float = Form(1.0),
    format: str = Form("wav"),
    sample_rate_hertz: int = Form(alias="sampleRateHertz", default=48000),
    cfg: TTSConfig = Depends(get_config),
) -> Response:
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty text")
    if voice not in cfg.speakers:
        raise HTTPException(status_code=400, detail=f"Unknown voice {voice}")
    if sample_rate_hertz not in (8000, 16000, 22050, 24000, 32000, 44100, 48000):
        raise HTTPException(status_code=400, detail="Unsupported sample rate")

    await ensure_model_loaded(cfg)

    try:
        wav_bytes: bytes = await asyncio.to_thread(
            synthesize, cfg, text.strip(), voice, sample_rate_hertz
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    headers = {"Content-Disposition": 'inline; filename="speech.wav"'}
    return Response(content=wav_bytes, media_type="audio/x-wav", headers=headers)


def register_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.include_router(router)

    return app


def main() -> None:
    setup_logging()

    app = register_app()

    uvicorn.run(
        app,
        host=os.getenv("SYNTHESIZER_SERVER_HOST", default="127.0.0.1"),
        port=int(os.getenv("SYNTHESIZER_SERVER_PORT", default="8194")),
    )


if __name__ == "__main__":
    main()
