import asyncio
import json
import re


async def get_playlist(url: str) -> tuple[str, list[dict]]:
    """Returns (playlist_title, tracks)."""
    cmd = [
        'yt-dlp',
        '--dump-single-json',
        '--no-download',
        url,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()

    if not stdout:
        return 'SoundCloud Playlist', []

    # stdout may have warnings mixed in — find the JSON line
    raw = stdout.decode()
    json_str = _extract_json(raw)
    if not json_str:
        return 'SoundCloud Playlist', []

    data = json.loads(json_str)
    title = data.get('title') or 'SoundCloud Playlist'
    entries = data.get('entries') or []

    tracks = []
    for i, e in enumerate(entries):
        if not e:
            continue
        tracks.append({
            'artist': e.get('uploader') or e.get('channel') or 'Unknown',
            'title': e.get('title') or f'Track {i+1}',
            'yandex_id': None,
            'available': True,
            'url': e.get('webpage_url') or e.get('url'),
            'duration_ms': int(e['duration'] * 1000) if e.get('duration') else None,
            'album': title,
            'year': None,
        })
    return title, tracks


def _extract_json(text: str) -> str | None:
    """Extract the last JSON object line from output that may contain warnings."""
    for line in reversed(text.strip().split('\n')):
        line = line.strip()
        if line.startswith('{'):
            return line
    return None
