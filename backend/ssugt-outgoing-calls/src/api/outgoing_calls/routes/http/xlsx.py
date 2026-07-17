import asyncio
import json
import traceback
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from starlette import status
from urllib.parse import quote

from starlette.responses import Response

from api.outgoing_calls.logger import logger
from api.outgoing_calls.services.xlsx import (
    convert_to_xlsx,
    ConcatColumnConfig,
    merge_tables,
)

router = APIRouter()


@router.post("/normalize_xlsx/")
async def normalize_xlsx(file: UploadFile = File(...), body: str = Form(default="[]")):
    file_bytes = await file.read()

    try:
        output_bytes = await asyncio.to_thread(
            convert_to_xlsx, file_bytes, file.filename
        )

        concat_columns = json.loads(body)

        concat_columns = [
            ConcatColumnConfig(**concat_column) for concat_column in concat_columns
        ]

        output_bytes = await asyncio.to_thread(
            merge_tables, output_bytes, concat_columns
        )
    except Exception:
        logger.warning(traceback.format_exc())

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error"},
        )

    filename = f"{Path(file.filename).stem}.xlsx"
    quoted_filename = quote(filename)

    return Response(
        content=output_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quoted_filename}"
        },
    )
