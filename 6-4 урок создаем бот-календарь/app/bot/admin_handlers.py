from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import admin_menu
from app.bot.messages import ADMIN_ONLY
from app.config.settings import load_settings

router = Router()


def _is_admin(telegram_id: int) -> bool:
    settings = load_settings()
    return telegram_id in settings.admin_telegram_ids


@router.message(Command("admin"))
async def admin(message: Message) -> None:
    if not message.from_user or not _is_admin(message.from_user.id):
        await message.answer(ADMIN_ONLY)
        return

    await message.answer("Админ-меню MeetMaster.", reply_markup=admin_menu())

