from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.bot.keyboards import main_menu
from app.bot.messages import HELP, UNKNOWN_ACTION, WELCOME

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(WELCOME, reply_markup=main_menu())


@router.message(Command("my_id"))
async def my_telegram_id(message: Message) -> None:
    if not message.from_user:
        await message.answer("Не удалось определить Telegram ID.")
        return

    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")


@router.message(lambda message: message.text == "Помощь")
async def help_message(message: Message) -> None:
    await message.answer(HELP, reply_markup=main_menu())


@router.message(lambda message: message.text == "Записаться на встречу")
async def start_booking(message: Message) -> None:
    await message.answer(
        "Сценарий записи будет добавлен на следующем этапе. "
        "Правила записи уже вынесены в отдельный сервис.",
        reply_markup=main_menu(),
    )


@router.message(lambda message: message.text == "Мои заявки")
async def my_requests(message: Message) -> None:
    await message.answer(
        "Список заявок будет подключен после реализации хранения в базе.",
        reply_markup=main_menu(),
    )


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(UNKNOWN_ACTION, reply_markup=main_menu())
