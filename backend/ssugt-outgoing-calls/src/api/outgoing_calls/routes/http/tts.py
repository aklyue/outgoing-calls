import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import Response

from api.outgoing_calls.deps import ApiClientMarker, IamTokenFetcherMarker
from api.outgoing_calls.logger import logger
from api.outgoing_calls.schemas import SynthesizeSchema
from api.outgoing_calls.services.tts.manager import is_stt_available, synthesize_speech
from api.outgoing_calls.services.tts.yandex import (
    IamTokenFetcher,
    get_yandex_cloud_balance,
)

router = APIRouter()


@router.get("/balance/")
async def retrieve_balance(
    api_client: aiohttp.ClientSession = Depends(ApiClientMarker),
    fetch_iam_token: IamTokenFetcher = Depends(IamTokenFetcherMarker),
):
    try:
        # iam_token = await fetch_iam_token(api_client)
        iam_token = 'iam-token'
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"IAM Error: {str(e)}"
        )

    # Защищаем запрос баланса от сетевых сбоев СГУГиТа
    try:
        balance = await get_yandex_cloud_balance(client=api_client, iam_token=iam_token)
    except (aiohttp.ClientConnectorError, aiohttp.ClientError) as e:
        # Ошибка сети/DNS не должна ронять приложение.
        # Вместо 500-й ошибки отдаем понятный статус.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Yandex Billing API unavailable due to local network/DNS failure: {str(e)}"
        )

    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Billing account not found or access denied"
        )

    return {"balance": balance}


@router.get("/synthesizers/")
async def retrieve_synthesizers():
    tts_types = ["ssugt", "yandex", "edge-tts"]

    synthesizers = [
        tts_type for tts_type in tts_types if await is_stt_available(tts_type=tts_type)  # type: ignore[arg-type]
    ]

    return synthesizers


@router.post("/synthesize/")
async def do_synthesize(
    synthesize: SynthesizeSchema,
    api_client: aiohttp.ClientSession = Depends(ApiClientMarker),
    fetch_iam_token: IamTokenFetcher = Depends(IamTokenFetcherMarker),
):
    try:
        iam_token = await fetch_iam_token(api_client)
        # iam_token = "iam_token"

        synthesized_speech, _ = await synthesize_speech(
            tts_type=synthesize.type_,  # type: ignore[arg-type]
            client=api_client,
            iam_token=iam_token,
            text=synthesize.text,
        )

        return Response(
            content=synthesized_speech,
            media_type="audio/wav",
            headers={"Content-Disposition": 'inline; filename="speech.wav"'},
        )
    except RuntimeError as e:
        logger.warning("Failed to synthesized speech: %s", e)

        raise HTTPException(status_code=400, detail="Synthesized failed")
