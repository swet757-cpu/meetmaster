from aiogram import Bot
from aiogram.types import BotCommand


BOT_COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="book", description="Новая встреча"),
    BotCommand(command="requests", description="Мои встречи"),
    BotCommand(command="help", description="Помощь"),
    BotCommand(command="my_id", description="Мой Telegram ID"),
    BotCommand(command="admin", description="Админ-меню"),
]


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(BOT_COMMANDS)

