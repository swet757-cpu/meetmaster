import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from app.config import get_settings


async def main() -> None:
    settings = get_settings()
    session = AiohttpSession(proxy=settings.telegram_proxy) if settings.telegram_proxy else None
    bot = Bot(settings.bot_token, session=session)

    try:
        me = await bot.get_me()
    finally:
        await bot.session.close()

    print("Связь с Telegram API есть.")
    print(f"Бот: @{me.username}")


if __name__ == "__main__":
    asyncio.run(main())
