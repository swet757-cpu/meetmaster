# MeetMaster Telegram Mini App

Дата: 2026-05-14

## Что добавлено

Mini App добавлен как отдельное дополнение к существующему боту.

Старый бот продолжает работать через aiogram polling. Mini App запускается отдельно через FastAPI и не заменяет старый сценарий записи.

## Новые части проекта

```text
app/mini_app/api.py
app/services/telegram_webapp_auth.py
app/services/mini_app_booking_service.py
mini_app/frontend/index.html
mini_app/frontend/styles.css
mini_app/frontend/app.js
Dockerfile.miniapp
docker-compose.miniapp.yml
```

## Что умеет первая версия

- проверять Telegram WebApp `initData`;
- показывать доступные даты;
- показывать допустимые длительности;
- показывать свободные слоты;
- создавать заявку на встречу;
- сохранять заявку в существующую базу;
- уведомлять администраторов через Telegram;
- показывать пользователю список его заявок;
- открываться как статический интерфейс внутри Telegram Mini App.

## API

```text
GET  /api/me
GET  /api/booking/dates
GET  /api/booking/durations
GET  /api/booking/slots?target_date=YYYY-MM-DD&duration=45
POST /api/booking/requests
GET  /api/booking/my-requests
```

Запросы, которые относятся к пользователю, должны передавать заголовок:

```text
X-Telegram-Init-Data: <Telegram WebApp initData>
```

## Локальный запуск backend

Сначала установить зависимости:

```powershell
.\.venv\Scripts\pip install -e .
```

Для локальной разработки можно временно включить dev-режим в `.env`:

```env
MINI_APP_DEV_MODE=true
MINI_APP_DEV_TELEGRAM_ID=8695348072
```

Запуск API:

```powershell
.\.venv\Scripts\python -m uvicorn app.mini_app.api:app --reload --host 127.0.0.1 --port 8080
```

Открыть:

```text
http://127.0.0.1:8080/
```

Для быстрой локальной проверки на порту `8090` добавлен скрипт:

```powershell
.\scripts\run_mini_app_local.ps1
```

Он запускает Mini App в dev-режиме с локальной SQLite-базой:

```text
local_data/mini_app_local.db
```

После запуска открыть:

```text
http://127.0.0.1:8090/
```

## Проверка

```powershell
.\.venv\Scripts\python -m unittest discover -s tests
.\.venv\Scripts\python -m compileall app tests mini_app
.\.venv\Scripts\python -m ruff check app tests
```

На момент добавления Mini App:

```text
26 tests OK
```

## Подключение к боту

В `.env` нужно указать публичный HTTPS URL Mini App:

```env
MINI_APP_URL=https://your-domain.example
```

После этого пользователь сможет открыть Mini App командой:

```text
/mini_app
```

Бот отправит inline-кнопку `Открыть календарь`.

## Запуск на сервере рядом с ботом

Mini App можно поднять отдельным compose-файлом:

```bash
cd /opt/meetmaster/app
docker compose -f docker-compose.yml -f docker-compose.miniapp.yml up -d --build
```

Сервис `miniapp` слушает только localhost:

```text
127.0.0.1:8080
```

Для Telegram нужен HTTPS. Поэтому перед Mini App нужен reverse proxy, например Caddy или Nginx, с доменом и TLS.

## Важное

На сервере мало места. Перед сборкой Mini App проверить:

```bash
df -h /
docker system df
```

Не удалять Supabase, n8n и существующие Docker volumes без отдельной проверки.

## Что дальше

Следующий этап:

1. Выбрать домен или поддомен для Mini App.
2. Настроить HTTPS reverse proxy.
3. Указать `MINI_APP_URL` в `.env`.
4. Проверить открытие внутри Telegram.
5. После проверки можно добавить кнопку Mini App в главное меню бота.
