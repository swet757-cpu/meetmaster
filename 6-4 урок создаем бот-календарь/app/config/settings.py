from dataclasses import dataclass
from datetime import time
import os
from pathlib import Path


def _load_env_file(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _parse_time(value: str) -> time:
    hours, minutes = value.split(":", maxsplit=1)
    return time(hour=int(hours), minute=int(minutes))


def _parse_int_list(value: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "да"}


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_telegram_ids: tuple[int, ...]
    telegram_force_ipv4: bool
    database_url: str
    google_calendar_enabled: bool
    google_calendar_id: str
    google_oauth_client_secret_file: str
    google_oauth_token_file: str
    timezone: str
    workday_start: time
    workday_end: time
    min_notice_days: int
    buffer_minutes: int
    allowed_durations: tuple[int, ...]
    log_level: str


def load_settings() -> Settings:
    _load_env_file()
    return Settings(
        bot_token=os.environ.get("BOT_TOKEN", ""),
        admin_telegram_ids=_parse_int_list(os.environ.get("ADMIN_TELEGRAM_IDS", "")),
        telegram_force_ipv4=_parse_bool(os.environ.get("TELEGRAM_FORCE_IPV4", "true")),
        database_url=os.environ.get("DATABASE_URL", ""),
        google_calendar_enabled=_parse_bool(os.environ.get("GOOGLE_CALENDAR_ENABLED", "false")),
        google_calendar_id=os.environ.get("GOOGLE_CALENDAR_ID", "primary"),
        google_oauth_client_secret_file=os.environ.get(
            "GOOGLE_OAUTH_CLIENT_SECRET_FILE",
            "./credentials/google_client_secret.json",
        ),
        google_oauth_token_file=os.environ.get(
            "GOOGLE_OAUTH_TOKEN_FILE",
            "./credentials/google_token.json",
        ),
        timezone=os.environ.get("TIMEZONE", "Europe/Moscow"),
        workday_start=_parse_time(os.environ.get("WORKDAY_START", "09:00")),
        workday_end=_parse_time(os.environ.get("WORKDAY_END", "17:00")),
        min_notice_days=int(os.environ.get("MIN_NOTICE_DAYS", "1")),
        buffer_minutes=int(os.environ.get("BUFFER_MINUTES", "15")),
        allowed_durations=_parse_int_list(os.environ.get("ALLOWED_DURATIONS", "30,45,60")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
