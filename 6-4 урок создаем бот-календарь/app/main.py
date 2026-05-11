import asyncio
import logging

from aiogram import Dispatcher

from app.bot.admin_handlers import router as admin_router
from app.bot.factory import create_bot
from app.bot.user_handlers import router as user_router
from app.config.settings import load_settings


async def main() -> None:
    settings = load_settings()
    logging.basicConfig(level=settings.log_level)

    bot = create_bot(settings)
    dispatcher = Dispatcher()
    dispatcher.include_router(user_router)
    dispatcher.include_router(admin_router)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
