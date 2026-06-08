import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from mutagen import File as MutagenFile

router = APIRouter()

AUDIO_EXTENSIONS = ('.mp3', '.flac', '.m4a', '.ogg', '.wav', '.aac')


def _safe_path(music_path: str, rel: str) -> str:
    full = os.path.realpath(os.path.join(music_path, rel))
    if not full.startswith(os.path.realpath(music_path) + os.sep) and \
       full != os.path.realpath(music_path):
        raise HTTPException(403, "Access denied")
    return full


def _format_quality(filepath: str, audio) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.flac':
        return 'FLAC'
    bitrate = getattr(getattr(audio, 'info', None), 'bitrate', 0)
    if bitrate:
        return f'MP3 {round(bitrate / 1000)}'
    return ext.lstrip('.').upper()


def _read_track_info(filepath: str, rel_path: str) -> dict:
    filename = os.path.basename(filepath)
    size = os.path.getsize(filepath)
    info = {
        'filename': filename,
        'path': rel_path,
        'title': '',
        'artist': '',
        'album': '',
        'duration': 0,
        'size': size,
        'quality': '',
    }
    try:
        audio = MutagenFile(filepath, easy=True)
        if audio is not None:
            info['title'] = (audio.get('title') or [''])[0]
            info['artist'] = (audio.get('artist') or [''])[0]
            info['album'] = (audio.get('album') or [''])[0]
            info['duration'] = int(getattr(audio.info, 'length', 0))
            info['quality'] = _format_quality(filepath, audio)
    except Exception:
        pass

    if not info['title']:
        stem = os.path.splitext(filename)[0]
        if ' - ' in stem:
            parts = stem.split(' - ', 1)
            info['artist'] = info['artist'] or parts[0].strip()
            info['title'] = parts[1].strip()
        else:
            info['title'] = stem

    return info


@router.get("/")
async def get_library():
    music_path = os.environ.get("MUSIC_PATH", "/music")
    playlists = []
    ungrouped = []

    for entry in sorted(os.scandir(music_path), key=lambda e: e.name):
        if entry.is_dir():
            tracks = []
            for f in sorted(os.scandir(entry.path), key=lambda e: e.name):
                if f.is_file() and f.name.lower().endswith(AUDIO_EXTENSIONS):
                    rel = f"{entry.name}/{f.name}"
                    tracks.append(_read_track_info(f.path, rel))
            if tracks:
                playlists.append({'name': entry.name, 'tracks': tracks})
        elif entry.is_file() and entry.name.lower().endswith(AUDIO_EXTENSIONS):
            ungrouped.append(_read_track_info(entry.path, entry.name))

    return {'playlists': playlists, 'ungrouped': ungrouped}


@router.get("/stream")
async def stream_file(path: str):
    music_path = os.environ.get("MUSIC_PATH", "/music")
    filepath = _safe_path(music_path, path)
    if not os.path.isfile(filepath):
        raise HTTPException(404, "File not found")
    return FileResponse(filepath)


@router.delete("/file")
async def delete_file(path: str):
    music_path = os.environ.get("MUSIC_PATH", "/music")
    filepath = _safe_path(music_path, path)
    if not os.path.isfile(filepath):
        raise HTTPException(404, "File not found")
    os.remove(filepath)
    return {"ok": True}


@router.get("/files")
async def list_files():
    music_path = os.environ.get("MUSIC_PATH", "/music")
    files = []
    for filename in sorted(os.listdir(music_path)):
        if filename.lower().endswith(AUDIO_EXTENSIONS):
            full = os.path.join(music_path, filename)
            if os.path.isfile(full):
                files.append({'filename': filename, 'size': os.path.getsize(full)})
    return files
