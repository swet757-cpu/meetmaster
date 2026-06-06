from __future__ import annotations

import logging
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "bot_hidden.log"
PID_PATH = BASE_DIR / "bot.pid"
TOKEN_ENV_NAME = "TELEGRAM_BOT_TOKEN"


def configure_logging() -> None:
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )


def main() -> int:
    os.chdir(BASE_DIR)
    configure_logging()

    if not os.getenv(TOKEN_ENV_NAME):
        logging.error("TELEGRAM_BOT_TOKEN is not set. Bot was not started.")
        return 2

    PID_PATH.write_text(str(os.getpid()), encoding="utf-8")

    try:
        import main as bot_app

        bot_app.init_db()
        logging.info("Bot started in hidden mode.")
        bot_app.bot.infinity_polling(skip_pending=True, logger_level=logging.INFO)
    except Exception:
        logging.exception("Bot stopped with an error.")
        return 1
    finally:
        logging.info("Bot process finished.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
