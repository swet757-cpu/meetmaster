# MeetMaster

Telegram-бот для согласования встреч и записи в Google Календарь.

## Текущий статус

Создан стартовый каркас проекта по документам:

- `ТЗ_MeetMaster_v1.md`
- `Архитектура_и_технологии_MeetMaster_v1.md`
- `Этапы_разработки_MeetMaster_v1.md`

## Стек

| Часть | Решение |
|---|---|
| Язык | Python |
| Telegram | aiogram |
| База данных | PostgreSQL |
| Календарь | Google Calendar API |
| Запуск MVP | polling |

## Локальная проверка без секретов

```powershell
python -m unittest discover -s tests
python -m compileall app tests
```

## Проверка Telegram-токена без вывода секрета

```powershell
.\.venv\Scripts\python -m app.tools.check_telegram
```

## Подключение Google Календаря

Google-синхронизация выключена, пока не подготовлен OAuth:

```env
GOOGLE_CALENDAR_ENABLED=false
```

Чтобы подготовить OAuth локально:

1. В Google Cloud включить Google Calendar API.
2. Создать OAuth Client для Desktop app.
3. Скачать JSON-файл и положить его сюда: `credentials/google_client_secret.json`.
4. Запустить:

```powershell
.\.venv\Scripts\python -m app.tools.google_oauth_setup
```

5. Войти в Google-аккаунт календаря и разрешить доступ.
6. После появления `credentials/google_token.json` включить синхронизацию:

```env
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CALENDAR_ID=primary
```

Папка `credentials/` добавлена в `.gitignore`. Эти файлы нельзя отправлять в чат или GitHub.

## Временный локальный запуск для проверки в Telegram

Основной бот работает через aiogram. Если на Windows есть сетевой таймаут `aiohttp`, можно проверить пользовательский сценарий через временный локальный runner:

```powershell
.\.venv\Scripts\python -m app.tools.local_test_bot
```

Остановить runner можно сочетанием `Ctrl+C`.

## Локальная проверка миграций базы

Команда ниже создает тестовую SQLite-базу только для проверки миграций. Рабочая база проекта остается PostgreSQL.

```powershell
New-Item -ItemType Directory -Force -Path local_data | Out-Null
$env:DATABASE_URL='sqlite+aiosqlite:///./local_data/alembic_check.db'
.\.venv\Scripts\python -m alembic upgrade head
```

## Настройки

Реальные секреты хранятся только в `.env`. В репозиторий добавлен только безопасный пример `.env.example`.

Нельзя отправлять в чат:

- Telegram Bot Token;
- пароль от сервера;
- пароль базы данных;
- Google OAuth credentials.
