import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter()

ALLOWED_EXTENSIONS = ('.mp3', '.flac', '.m4a', '.ogg')


@router.post("/")
async def upload_files(files: List[UploadFile] = File(...)):
    music_path = os.environ.get("MUSIC_PATH", "/music")
    saved = []
    for file in files:
        if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
            continue
        dest = os.path.join(music_path, os.path.basename(file.filename))
        with open(dest, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        saved.append(file.filename)
    return {"saved": saved}
