# PROJECT_LOG

## 2026-06-08 — Библиотека, плеер, дедупликация

### Изменения

**Библиотека (routers/library.py):**
- `GET /library/` — структура папок вместо плоского списка файлов
- Каждый трек включает: path, title, artist, album, duration, quality, size
- `GET /library/stream?path=` — FileResponse для стриминга аудио
- `DELETE /library/file?path=` — удаление файла
- Защита от path traversal через `os.realpath` + проверка prefix
- Баг: `if audio:` → `if audio is not None:` (mutagen наследует dict, falsy при пустых тегах)

**Метаданные (services/yandex.py):**
- Треки теперь несут: duration_ms, album, year
- После скачивания пишутся теги через mutagen (ID3 для MP3, FLAC tags для FLAC)
- Поддержка двух форматов URL: `/users/{user}/playlists/{id}` и `/playlists/{uuid}`
- UUID-плейлисты: `GET https://api.music.yandex.net/playlist/{uuid}` с OAuth

**SoundCloud (services/soundcloud.py):**
- Переход с `--flat-playlist --dump-json` на `--dump-single-json`
- Получаем реальное название плейлиста и полные метаданные треков
- `_extract_json()` — парсинг последней JSON-строки из вывода с warnings

**Дедупликация (services/downloader.py):**
- `_build_track_index()` — индекс `normalize(artist - title) → filepath` по всему /music
- Строится один раз в начале джоба
- При совпадении: hard link в папку нового плейлиста, source="library"
- Fallback: `shutil.copy2` если hard link невозможен (cross-device)
- `_normalize()`: lower + убрать пунктуацию + collapse spaces

**Загрузка (services/ytdlp.py):**
- `_unique_path()` — добавляет `(2)`, `(3)` при конфликте имён файлов
- `--add-metadata` флаг для yt-dlp загрузок
- Папка джоба передаётся как `output_folder` вместо music_path

**Структура папок:**
- Треки теперь в `music/{playlist_name}/Artist - Title.ext`
- Старые треки (из первого теста) лежат в `music/` как "Без плейлиста"

**UI (Library.jsx):**
- Коллапсируемые группы плейлистов
- Строка трека: play-кнопка | название / исполнитель | quality | size | duration | ⋮
- HTML5 audio плеер, один на страницу, переключается между треками
- Удаление: убирает трек из локального state без перезагрузки
- Контекстное меню (3 точки вертикально): "Удалить"
- Закрытие меню по клику вне

**Queue (TrackRow.jsx):**
- Добавлен source "library" → отображается "из библиотеки"

**docker-compose.yml:**
- Удалён устаревший атрибут `version`
- API маппится на порт 8080 (8000 занят tg-parser)

---

## 2026-06-07 — Инициализация проекта

### Создано

- Полная структура проекта
- docker-compose.yml — Navidrome + API + UI
- .env / .env.example / .gitignore
- backup.sh, README.md

**API:** FastAPI, все роутеры и сервисы, WebSocket для прогресса загрузок

**UI:** React + Vite + Tailwind, 4 страницы (Import, Queue, Library, Upload)

### Баги исправлены

- `UnboundLocalError: _ws_clients` в `_broadcast()` — добавлен `global _ws_clients`
- Яндекс UUID плейлисты — новый формат URL не парсился
- SoundCloud "Unknown — Unknown" — `--flat-playlist` не даёт метаданные
- Одинаковые имена файлов при SoundCloud импорте — все перезаписывали друг друга

### Решения

- Port 8000 занят tg-parser → MOMS API на 8080
- yandex-music-api (MarshalX) — наиболее актуальный Python-инструмент
- Spotify даёт только метаданные, треки качаются через yt-dlp YouTube search
- Beets отключён (добавить позже)
- UI обращается к API через `/api` (nginx proxy), без env vars
