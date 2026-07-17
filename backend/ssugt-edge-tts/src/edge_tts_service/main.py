import logging
import os

import uvicorn
from fastapi import FastAPI, Form, Response, HTTPException

from edge_tts_service.logger import setup_logging
from edge_tts_service.tts import synthesize, SUPPORTED_VOICES, VOICE_ALIASES
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="Edge TTS Synthesizer")


class TTSRequest(BaseModel):
    text: str
    lang: str = "ru-RU"
    voice: str = "ru-RU-SvetlanaNeural"
    speed: float = 1.0


@app.post("/speech/v1/tts:synthesize")
async def do_synthesize(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    # Resolve voice
    voice_name = VOICE_ALIASES.get(request.voice, request.voice)

    # Map speed to rate string
    rate_percent = int((request.speed - 1.0) * 100)
    rate_str = f"{'+' if rate_percent >= 0 else ''}{rate_percent}%"

    try:
        audio_bytes = await synthesize(
            text=request.text.strip(),
            voice=voice_name,
            rate=rate_str,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    return Response(content=audio_bytes, media_type="audio/wav")


@app.get("/voices")
async def list_voices():
    """Return the list of supported voices."""
    return {
        "voices": SUPPORTED_VOICES,
        "aliases": {k: v for k, v in VOICE_ALIASES.items()},
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


def main() -> None:
    setup_logging()

    uvicorn.run(
        app,
        host=os.getenv("EDGE_TTS_SERVER_HOST", default="127.0.0.1"),
        port=int(os.getenv("EDGE_TTS_SERVER_PORT", default="8195")),
    )


if __name__ == "__main__":
    main()
