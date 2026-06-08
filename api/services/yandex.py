import asyncio
import os
import re
import requests as _requests
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=4)

_API_HEADERS = {'X-Yandex-Music-Client': 'YandexMusicAPI'}


def _auth_headers(token: str) -> dict:
    return {**_API_HEADERS, 'Authorization': f'OAuth {token}'}


def _get_playlist_sync(url: str, token: str) -> tuple[str, list[dict]]:
    """Returns (playlist_title, tracks)."""
    # Format 1: /users/{user}/playlists/{kind}
    match = re.search(r'/users/([^/]+)/playlists/(\d+)', url)
    if match:
        from yandex_music import Client
        client = Client(token).init()
        user_id, playlist_id = match.group(1), int(match.group(2))
        playlist = client.users_playlists(playlist_id, user_login=user_id)
        title = playlist.title or 'Yandex Playlist'
        return title, _extract_tracks_from_ym(playlist.tracks)

    # Format 2: /playlists/{uuid}
    match = re.search(r'/playlists/([a-f0-9-]{36})', url)
    if match:
        uuid = match.group(1)
        r = _requests.get(
            f'https://api.music.yandex.net/playlist/{uuid}',
            headers=_auth_headers(token),
        )
        r.raise_for_status()
        data = r.json().get('result', {})
        title = data.get('title') or 'Yandex Playlist'
        return title, _extract_tracks_from_raw(data.get('tracks', []))

    raise ValueError(f"Cannot parse Yandex playlist URL: {url}")


def _extract_tracks_from_ym(track_shorts: list) -> list[dict]:
    tracks = []
    for ts in track_shorts:
        t = ts.track if hasattr(ts, 'track') else ts
        if t is None:
            continue
        album_data = t.albums[0] if t.albums else None
        tracks.append({
            'artist': ', '.join(a.name for a in t.artists) if t.artists else 'Unknown',
            'title': t.title or 'Unknown',
            'yandex_id': int(t.id),
            'available': t.available,
            'duration_ms': t.duration_ms,
            'album': album_data.title if album_data else None,
            'year': album_data.year if album_data else None,
        })
    return tracks


def _extract_tracks_from_raw(raw_tracks: list) -> list[dict]:
    tracks = []
    for item in raw_tracks:
        t = item.get('track') if isinstance(item, dict) and 'track' in item else item
        if not t:
            continue
        artist = ', '.join(a['name'] for a in t.get('artists', [])) or 'Unknown'
        album_data = (t.get('albums') or [{}])[0]
        tracks.append({
            'artist': artist,
            'title': t.get('title') or 'Unknown',
            'yandex_id': int(t['id']),
            'available': t.get('available', True),
            'duration_ms': t.get('durationMs'),
            'album': album_data.get('title'),
            'year': album_data.get('year'),
        })
    return tracks


async def get_playlist(url: str, token: str) -> tuple[str, list[dict]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _get_playlist_sync, url, token)


def _write_tags(filepath: str, title: str, artist: str, album: str, year: int = None):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.flac':
            from mutagen.flac import FLAC
            audio = FLAC(filepath)
            audio['title'] = title
            audio['artist'] = artist
            audio['album'] = album
            if year:
                audio['date'] = str(year)
            audio.save()
        else:
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, ID3NoHeaderError
            try:
                tags = ID3(filepath)
            except ID3NoHeaderError:
                tags = ID3()
            tags['TIT2'] = TIT2(encoding=3, text=title)
            tags['TPE1'] = TPE1(encoding=3, text=artist)
            tags['TALB'] = TALB(encoding=3, text=album)
            if year:
                tags['TDRC'] = TDRC(encoding=3, text=str(year))
            tags.save(filepath)
    except Exception:
        pass  # tagging is best-effort


def _download_sync(track_data: dict, output_folder: str, token: str) -> str:
    from yandex_music import Client
    client = Client(token).init()
    yandex_id = track_data['yandex_id']
    track = client.tracks([yandex_id])[0]

    if not track.available:
        raise Exception("Track not available")

    download_info = track.get_download_info()
    if not download_info:
        raise Exception("No download info")

    best = None
    for di in download_info:
        if di.codec == 'flac':
            best = di
            break
        if best is None or di.bitrate_in_kbps > best.bitrate_in_kbps:
            best = di

    ext = 'flac' if best.codec == 'flac' else 'mp3'
    safe_artist = re.sub(r'[<>:"/\\|?*]', '_', track_data['artist'])
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', track_data['title'])
    filepath = os.path.join(output_folder, f"{safe_artist} - {safe_title}.{ext}")

    best.download(filepath)

    _write_tags(
        filepath,
        title=track_data['title'],
        artist=track_data['artist'],
        album=track_data.get('album') or '',
        year=track_data.get('year'),
    )
    return filepath


async def download_track(track_data: dict, output_folder: str, token: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _download_sync, track_data, output_folder, token)
