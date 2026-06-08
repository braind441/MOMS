import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import downloader

router = APIRouter()


class ImportRequest(BaseModel):
    url: str


def detect_source(url: str) -> str:
    if 'music.yandex.ru' in url:
        return 'yandex'
    if 'spotify.com' in url:
        return 'spotify'
    if 'soundcloud.com' in url:
        return 'soundcloud'
    raise ValueError(f"Unsupported URL: {url}")


@router.post("/import")
async def import_playlist(req: ImportRequest):
    try:
        source = detect_source(req.url)
    except ValueError as e:
        raise HTTPException(400, str(e))

    try:
        if source == 'yandex':
            from services import yandex
            token = os.environ.get("YANDEX_TOKEN")
            name, tracks = await yandex.get_playlist(req.url, token)
        elif source == 'spotify':
            from services import spotify
            tracks = await spotify.get_playlist_tracks(req.url)
            name = "Spotify Playlist"
        elif source == 'soundcloud':
            from services import soundcloud
            name, tracks = await soundcloud.get_playlist(req.url)

        if not tracks:
            raise HTTPException(400, "Playlist is empty or could not be parsed")

        job_id = await downloader.create_job(name, source, tracks)
        return {"job_id": job_id, "tracks": len(tracks), "source": source, "name": name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
