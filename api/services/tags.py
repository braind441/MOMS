import os


def write_tags(filepath: str, title: str, artist: str, album: str = None, year=None):
    """Write basic tags into an audio file. Best-effort (errors are swallowed).

    Used after every successful download regardless of source (yandex / yt-dlp),
    so files always carry correct metadata from the playlist, not just from the
    direct-Yandex path.
    """
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.flac':
            from mutagen.flac import FLAC
            audio = FLAC(filepath)
            audio['title'] = title
            audio['artist'] = artist
            if album:
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
            if album:
                tags['TALB'] = TALB(encoding=3, text=album)
            if year:
                tags['TDRC'] = TDRC(encoding=3, text=str(year))
            tags.save(filepath)
    except Exception:
        pass  # tagging is best-effort
