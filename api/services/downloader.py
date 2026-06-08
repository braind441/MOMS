import asyncio
import json
import os
import re
import shutil
import uuid
from typing import Dict, Set

from fastapi import WebSocket
from models.playlist import Job
from models.track import Track, TrackStatus

_jobs: Dict[str, Job] = {}
_ws_clients: Set[WebSocket] = set()

AUDIO_EXTENSIONS = ('.mp3', '.flac', '.m4a', '.ogg', '.wav', '.aac')


def _safe_folder(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip() or 'Playlist'


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def _build_track_index(music_path: str) -> dict[str, str]:
    """Scan all audio files and return {normalized_key: filepath}."""
    index = {}
    for root, dirs, files in os.walk(music_path):
        dirs.sort()
        for filename in sorted(files):
            if not filename.lower().endswith(AUDIO_EXTENSIONS):
                continue
            stem = os.path.splitext(filename)[0]
            key = _normalize(stem)
            filepath = os.path.join(root, filename)
            if key not in index:
                index[key] = filepath
    return index


def _find_existing(artist: str, title: str, index: dict[str, str]) -> str | None:
    key = _normalize(f"{artist} - {title}")
    if key in index:
        return index[key]
    # Also try just title in case artist is slightly different
    key_title = _normalize(title)
    for k, v in index.items():
        if key_title and key_title in k:
            return v
    return None


def _link_or_copy(src: str, dst_folder: str, filename: str) -> str:
    dst = os.path.join(dst_folder, filename)
    if os.path.exists(dst):
        return dst
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)
    return dst


def get_jobs() -> Dict[str, Job]:
    return _jobs


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def add_ws_client(ws: WebSocket):
    _ws_clients.add(ws)


def remove_ws_client(ws: WebSocket):
    _ws_clients.discard(ws)


async def _broadcast(data: dict):
    global _ws_clients
    msg = json.dumps(data)
    dead = set()
    for ws in list(_ws_clients):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _ws_clients -= dead


async def create_job(name: str, source: str, raw_tracks: list[dict]) -> str:
    job_id = str(uuid.uuid4())
    folder = _safe_folder(name)
    tracks = [
        Track(
            id=str(uuid.uuid4()),
            artist=t['artist'],
            title=t['title'],
            yandex_id=t.get('yandex_id'),
            available=t.get('available', True),
            sc_url=t.get('url'),
            duration_ms=t.get('duration_ms'),
            album=t.get('album'),
            year=t.get('year'),
        )
        for t in raw_tracks
    ]
    job = Job(id=job_id, name=name, source=source, folder=folder, tracks=tracks)
    _jobs[job_id] = job

    music_path = os.environ.get("MUSIC_PATH", "/music")
    output_folder = os.path.join(music_path, folder)
    os.makedirs(output_folder, exist_ok=True)

    asyncio.create_task(_run_job(job_id, music_path, output_folder))
    return job_id


async def _run_job(job_id: str, music_path: str, output_folder: str):
    from services import yandex, ytdlp

    job = _jobs[job_id]
    token = os.environ.get("YANDEX_TOKEN")

    # Build index of existing tracks once before starting
    track_index = _build_track_index(music_path)

    for track in job.tracks:
        track.status = TrackStatus.downloading
        await _broadcast({"type": "update", "job_id": job_id, "track": track.model_dump()})

        # Check if already in library
        existing = _find_existing(track.artist, track.title, track_index)
        if existing and not existing.startswith(output_folder):
            filename = os.path.basename(existing)
            _link_or_copy(existing, output_folder, filename)
            track.status = TrackStatus.done
            track.source = "library"
            track_index[_normalize(f"{track.artist} - {track.title}")] = os.path.join(output_folder, filename)
            await _broadcast({"type": "update", "job_id": job_id, "track": track.model_dump()})
            continue

        success = False

        # Try Yandex first
        if track.yandex_id and track.available and token:
            try:
                filepath = await yandex.download_track(track.model_dump(), output_folder, token)
                track.status = TrackStatus.done
                track.source = "yandex"
                track_index[_normalize(f"{track.artist} - {track.title}")] = filepath
                success = True
            except Exception as e:
                track.error = str(e)

        # Try direct SoundCloud URL
        if not success and track.sc_url:
            try:
                result = await ytdlp.download_by_url(track.sc_url, track.artist, track.title, output_folder)
                if result:
                    track.status = TrackStatus.done
                    track.source = "soundcloud"
                    track_index[_normalize(f"{track.artist} - {track.title}")] = result
                    success = True
            except Exception as e:
                track.error = str(e)

        # Fallback: yt-dlp YouTube search
        if not success:
            try:
                result = await ytdlp.search_and_download(track.artist, track.title, output_folder)
                if result:
                    track.status = TrackStatus.done
                    track.source = "youtube"
                    track_index[_normalize(f"{track.artist} - {track.title}")] = result
                    success = True
            except Exception as e:
                track.error = str(e)

        if not success and track.status == TrackStatus.downloading:
            track.status = TrackStatus.not_found

        await _broadcast({"type": "update", "job_id": job_id, "track": track.model_dump()})


async def retry_track(job_id: str, track_id: str, url: str):
    from services import ytdlp

    job = _jobs.get(job_id)
    if not job:
        return
    track = next((t for t in job.tracks if t.id == track_id), None)
    if not track:
        return

    music_path = os.environ.get("MUSIC_PATH", "/music")
    output_folder = os.path.join(music_path, job.folder)

    track.status = TrackStatus.downloading
    await _broadcast({"type": "update", "job_id": job_id, "track": track.model_dump()})

    result = await ytdlp.download_by_url(url, track.artist, track.title, output_folder)
    track.status = TrackStatus.done if result else TrackStatus.not_found
    if result:
        track.source = "manual"
    await _broadcast({"type": "update", "job_id": job_id, "track": track.model_dump()})
