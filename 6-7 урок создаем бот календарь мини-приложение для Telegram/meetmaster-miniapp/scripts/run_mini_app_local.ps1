$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$env:DATABASE_URL = "sqlite+aiosqlite:///./local_data/mini_app_review.db"
$env:BOT_TOKEN = "123456:ABCDEF"
$env:ADMIN_TELEGRAM_IDS = ""
$env:MINI_APP_DEV_MODE = "true"
$env:MINI_APP_DEV_TELEGRAM_ID = "8695348072"
$env:MINI_APP_URL = "http://127.0.0.1:8090"

& ".\.venv\Scripts\python.exe" -m uvicorn app.mini_app.api:app --host 127.0.0.1 --port 8090
