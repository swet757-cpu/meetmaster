from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Записаться на встречу")],
            [KeyboardButton(text="Мои заявки"), KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Заявки на согласовании")],
            [KeyboardButton(text="Настройки записи"), KeyboardButton(text="Статистика")],
            [KeyboardButton(text="Закрыть день"), KeyboardButton(text="Открыть день")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Админ-меню",
    )

