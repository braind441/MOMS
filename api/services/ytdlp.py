import asyncio
import json
import os
import re


def _safe_name(artist: str, title: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', f"{artist} - {title}").strip()


def _unique_path(folder: str, base: str, ext: str) -> str:
    path = os.path.join(folder, f"{base}.{ext}")
    if not os.path.exists(path):
        return path
    i = 2
    while os.path.exists(os.path.join(folder, f"{base} ({i}).{ext}")):
        i += 1
    return os.path.join(folder, f"{base} ({i}).{ext}")


async def search_and_download(artist: str, title: str, output_folder: str) -> str | None:
    safe = _safe_name(artist, title)
    dest = _unique_path(output_folder, safe, 'mp3')
    output_template = os.path.splitext(dest)[0] + '.%(ext)s'

    cmd = [
        'yt-dlp',
        f'ytsearch1:{artist} {title}',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '320K',
        '--add-metadata',
        '--output', output_template,
        '--no-playlist',
        '--quiet',
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    if proc.returncode == 0 and os.path.exists(dest):
        return dest
    return None


async def download_by_url(url: str, artist: str, title: str, output_folder: str) -> str | None:
    safe = _safe_name(artist, title)
    dest = _unique_path(output_folder, safe, 'mp3')
    output_template = os.path.splitext(dest)[0] + '.%(ext)s'

    cmd = [
        'yt-dlp',
        url,
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '320K',
        '--add-metadata',
        '--output', output_template,
        '--no-playlist',
        '--quiet',
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    if proc.returncode == 0 and os.path.exists(dest):
        return dest
    return None


async def search_tracks(artist: str, title: str) -> list[dict]:
    results = []
    for source, prefix in [('youtube', 'ytsearch3'), ('soundcloud', 'scsearch3')]:
        cmd = [
            'yt-dlp',
            f'{prefix}:{artist} {title}',
            '--dump-json',
            '--no-download',
            '--quiet',
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if stdout:
            for line in stdout.decode().strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    results.append({
                        'source': source,
                        'url': data.get('webpage_url'),
                        'title': data.get('title'),
                        'uploader': data.get('uploader'),
                        'duration': data.get('duration'),
                    })
                except Exception:
                    pass
    return results
