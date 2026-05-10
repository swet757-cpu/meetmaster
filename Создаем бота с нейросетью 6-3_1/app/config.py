import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    bot_token: str
    work_dir: Path
    telegram_proxy: str | None
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str | None


def get_settings() -> Settings:
    _load_dotenv(Path(".env"))
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("Создайте переменную окружения BOT_TOKEN с токеном Telegram-бота.")

    work_dir = Path(os.getenv("BOT_WORK_DIR", "bot_files")).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    telegram_proxy = os.getenv("TELEGRAM_PROXY") or None
    openai_api_key = os.getenv("OPENAI_API_KEY") or None
    openai_model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    openai_base_url = os.getenv("OPENAI_BASE_URL") or None
    return Settings(
        bot_token=bot_token,
        work_dir=work_dir,
        telegram_proxy=telegram_proxy,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_base_url=openai_base_url,
    )


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
