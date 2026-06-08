# MOMS — My Own Music Server

## Цель проекта
Self-hosted музыкальная система на VPS. Стек: Navidrome (медиасервер) +
веб-интерфейс управления (скачивание, импорт плейлистов, библиотека).
iOS: Yuzic (стриминг + офлайн на iPhone), OnePlayer (перенос на Apple Watch).

---

## Стек

- **Navidrome** — медиасервер, Subsonic API
- **yandex-music-api** (MarshalX, Python) — загрузка с Яндекс.Музыки
- **yt-dlp** — загрузка с YouTube, SoundCloud, fallback
- **spotipy** — Spotify Web API (только метаданные плейлистов)
- **mutagen** — чтение/запись ID3/FLAC тегов
- **FastAPI** — бэкенд
- **React (Vite) + Tailwind CSS** — фронтенд
- **Docker Compose** — оркестрация
- **rsync** — бэкап музыки на ноутбук

---

## Порты

- Navidrome: **4533**
- MOMS API: **8080** (внутри контейнера 8000; 8000 занят tg-parser)
- MOMS UI: **3000** (nginx, proxy /api/ → http://api:8000/)
- VPS IP: **95.85.229.224**

---

## Архитектура

- `/music` volume — общий между navidrome и api
- Треки хранятся в `music/{playlist_name}/Artist - Title.ext`
- Ungrouped треки (старый импорт) лежат в `music/` напрямую
- Жёсткие ссылки (hard links) для дедупликации: один файл — несколько папок

---

## Структура проекта

```
moms/
├── docker-compose.yml
├── .env                    # токены (в .gitignore)
├── .env.example
├── .gitignore
├── backup.sh
├── README.md
├── CLAUDE.md
├── PROJECT_LOG.md
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── routers/
│   │   ├── import_playlist.py   # POST /playlist/import
│   │   ├── download.py          # GET/WS /downloads/*
│   │   ├── library.py           # GET / stream / delete
│   │   └── upload.py            # POST /upload/
│   ├── services/
│   │   ├── downloader.py        # очередь, WebSocket broadcast, дедупликация
│   │   ├── yandex.py            # yandex-music-api + запись тегов
│   │   ├── ytdlp.py             # yt-dlp wrapper
│   │   ├── spotify.py           # spotipy (только метаданные)
│   │   └── soundcloud.py        # yt-dlp --dump-single-json
│   └── models/
│       ├── track.py             # Track + TrackStatus
│       └── playlist.py          # Job (id, name, source, folder, tracks)
├── ui/
│   ├── Dockerfile
│   ├── nginx.conf               # proxy /api/ → http://api:8000/
│   └── src/
│       ├── App.jsx              # tab navigation
│       ├── pages/
│       │   ├── Import.jsx       # URL input → POST /playlist/import
│       │   ├── Queue.jsx        # WebSocket real-time статусы
│       │   ├── Library.jsx      # плейлисты + треки + плеер + удаление
│       │   └── Upload.jsx       # drag & drop
│       └── components/
│           ├── TrackRow.jsx     # строка в Queue
│           └── SourcePicker.jsx # модальный поиск альтернативного источника
└── music/                       # .gitignore
```

---

## API endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /playlist/import | Импорт плейлиста (yandex/spotify/soundcloud) |
| GET | /downloads/jobs | Список джобов |
| GET | /downloads/jobs/{id} | Статус джоба |
| GET | /downloads/jobs/{id}/tracks/{tid}/search | Поиск альтернативы |
| POST | /downloads/jobs/{id}/tracks/{tid}/retry | Скачать по URL |
| WS | /downloads/ws | Broadcast обновлений |
| GET | /library/ | Плейлисты + треки с метаданными |
| GET | /library/stream?path= | Стриминг аудиофайла |
| DELETE | /library/file?path= | Удалить файл |
| POST | /upload/ | Загрузить MP3/FLAC |
| GET | /health | Healthcheck |

---

## Форматы URL плейлистов

| Источник | Формат |
|----------|--------|
| Яндекс (пользователь) | `music.yandex.ru/users/{user}/playlists/{id}` |
| Яндекс (UUID) | `music.yandex.ru/playlists/{uuid}` → API: `/playlist/{uuid}` |
| Spotify | `open.spotify.com/playlist/{id}` |
| SoundCloud | `soundcloud.com/{user}/sets/{set}` |

---

## Ключевые решения

- **Яндекс UUID плейлисты**: `GET https://api.music.yandex.net/playlist/{uuid}` с OAuth токеном
- **SoundCloud**: `yt-dlp --dump-single-json` даёт название плейлиста и полные метаданные треков; `--flat-playlist` не даёт имена
- **Дедупликация**: перед скачиванием строится индекс `normalize(artist - title) → filepath` по всему `/music`; если найдено — hard link, source="library"
- **mutagen `if audio is not None`**: объект falsy при пустых тегах (наследует dict), поэтому не `if audio:`
- **yt-dlp уникальные имена**: `_unique_path()` добавляет `(2)`, `(3)` при конфликте имён
- **Теги Яндекс**: пишутся через mutagen после скачивания (ID3 для MP3, FLAC tags для FLAC)
- **port 8000 занят** tg-parser — MOMS API маппится на 8080
- **WebSocket broadcast**: глобальный `_ws_clients: Set[WebSocket]`, нужен `global _ws_clients` в `_broadcast()`

---

## Функциональность (реализовано)

### Импорт плейлиста
- Яндекс, Spotify, SoundCloud
- Реальное название плейлиста используется как имя папки и джоба
- Треки получают метаданные: artist, title, album, year, duration_ms

### Загрузка треков
- Приоритет: Яндекс → SoundCloud URL → YouTube search
- Дедупликация через индекс + hard links
- Теги пишутся в файл после скачивания

### Библиотека
- Структура: плейлисты (папки) + "Без плейлиста" (корень)
- Данные из тегов: title, artist, album, duration, quality (MP3 320 / FLAC), size
- Проигрывание через HTML5 audio + /library/stream
- Удаление файла без перезагрузки страницы (локальный state)
- Контекстное меню (3 точки): удалить

### Статусы треков
`pending` → `downloading` → `done` | `unavailable` | `not_found`
+ `source`: yandex | soundcloud | youtube | library | manual

### Beets
Отключён. Добавить позже если потребуется.

---

## Переменные окружения

```
YANDEX_TOKEN=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
MUSIC_PATH=/music
```

---

## Правила разработки

1. Новые функции — дополнять CLAUDE.md
2. Все изменения — в PROJECT_LOG.md
3. Тестировать перед отчётом
4. При планировании — предлагать план и ждать подтверждения
5. После завершения — коммитить на git
