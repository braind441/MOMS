from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services import downloader

router = APIRouter()


@router.get("/jobs")
async def list_jobs():
    return [
        {
            "id": job.id,
            "name": job.name,
            "source": job.source,
            "total": len(job.tracks),
            "done": sum(1 for t in job.tracks if t.status == "done"),
        }
        for job in downloader.get_jobs().values()
    ]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = downloader.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/jobs/{job_id}/tracks/{track_id}/search")
async def search_alternatives(job_id: str, track_id: str):
    job = downloader.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    track = next((t for t in job.tracks if t.id == track_id), None)
    if not track:
        raise HTTPException(404, "Track not found")
    from services import ytdlp
    return await ytdlp.search_tracks(track.artist, track.title)


class RetryRequest(BaseModel):
    url: str


@router.post("/jobs/{job_id}/tracks/{track_id}/retry")
async def retry_track(job_id: str, track_id: str, req: RetryRequest):
    await downloader.retry_track(job_id, track_id, req.url)
    return {"ok": True}


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    downloader.add_ws_client(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        downloader.remove_ws_client(ws)
