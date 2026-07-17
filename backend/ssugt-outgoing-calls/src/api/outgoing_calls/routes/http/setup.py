from fastapi import APIRouter

from api.outgoing_calls.routes.http.calls import router as calls_router
from api.outgoing_calls.routes.http.tts import router as tts_router
from api.outgoing_calls.routes.http.xlsx import router as xlsx_router


def register_http_router() -> APIRouter:
    router = APIRouter()

    router.include_router(calls_router)
    router.include_router(tts_router)
    router.include_router(xlsx_router)

    return router
