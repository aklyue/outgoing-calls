import os
import asyncio
from pathlib import Path

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()
UPLOAD_DIR = Path("/sounds/custom")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_file(*, file: UploadFile, dest_path: Path):
    contents = await file.read()
    await asyncio.to_thread(dest_path.write_bytes, contents)


async def remove_file(path: Path):
    def delete():
        os.remove(path)

    await asyncio.to_thread(delete)


async def file_exists(path: Path) -> bool:
    return await asyncio.to_thread(path.exists)


@router.get("/exists/{filename}")
async def is_exists_file(filename: str):
    filepath = UPLOAD_DIR / f"{filename}.wav"
    return await file_exists(filepath)


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...), filename: str = Form(...)):
    dest_path = UPLOAD_DIR / f"{filename}.wav"
    await save_file(file=file, dest_path=dest_path)

    return JSONResponse(content={"message": "File uploaded", "path": str(dest_path)})


@router.delete("/delete/{filename}")
async def delete_file(filename: str):
    filepath = UPLOAD_DIR / f"{filename}.wav"
    if not await file_exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    await remove_file(filepath)
    return JSONResponse(content={"message": "File deleted"})


def main() -> None:
    app = FastAPI()

    app.include_router(router)

    uvicorn.run(
        app,
        host=os.getenv("STORAGE_SERVER_HOST", default="127.0.0.1"),
        port=int(os.getenv("STORAGE_SERVER_PORT", default="8190")),
    )


if __name__ == "__main__":
    main()
