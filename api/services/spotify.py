import asyncio
import os
import re
from concurrent.futures import ThreadPoolExecutor


def _parse_playlist_id(url: str) -> str:
    match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
    if not match:
        raise ValueError(f"Cannot parse Spotify playlist URL: {url}")
    return match.group(1)


def _fetch_sync(url: str) -> list[dict]:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    ))
    playlist_id = _parse_playlist_id(url)
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    while results:
        for item in results['items']:
            t = item.get('track')
            if not t:
                continue
            tracks.append({
                'artist': ', '.join(a['name'] for a in t['artists']),
                'title': t['name'],
                'yandex_id': None,
                'available': True,
            })
        results = sp.next(results) if results['next'] else None
    return tracks


async def get_playlist_tracks(url: str) -> list[dict]:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, _fetch_sync, url)
