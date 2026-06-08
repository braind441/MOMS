# MOMS — My Own Music Server

Self-hosted музыкальный сервер: Navidrome + веб-интерфейс для загрузки плейлистов.

## Стек

- **Navidrome** :4533 — медиасервер, Subsonic API (для Yuzic/OnePlayer)
- **MOMS API** :8080 — FastAPI бэкенд
- **MOMS UI** :3000 — React фронтенд
- **yt-dlp + ffmpeg** — загрузка с YouTube/SoundCloud
- **yandex-music-api** — загрузка с Яндекс.Музыки

## Деплой на VPS

### 1. Подготовка VPS

```bash
apt update && apt install -y docker.io docker-compose-plugin git
```

### 2. Клонирование и настройка

```bash
git clone https://github.com/YOUR/moms.git
cd moms
cp .env.example .env
nano .env  # заполни токены
```

### 3. Запуск

```bash
docker compose up -d
```

### 4. Первый запуск Navidrome

Открой `http://vps-ip:4533` — создай admin-аккаунт.

### 5. Доступ

| Сервис | URL |
|--------|-----|
| MOMS UI | `http://vps-ip:3000` |
| MOMS API | `http://vps-ip:8080` |
| Navidrome | `http://vps-ip:4533` |

## Бэкап (с ноутбука)

```bash
./backup.sh user@vps-ip
```

Музыка синхронизируется в `~/moms-backup/music/`.

Настройка SSH-ключа:
```bash
ssh-keygen -t ed25519
ssh-copy-id user@vps-ip
```

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `YANDEX_TOKEN` | OAuth токен Яндекс.Музыки |
| `SPOTIFY_CLIENT_ID` | Spotify App Client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify App Client Secret |
