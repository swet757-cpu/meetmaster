from datetime import date

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.services.slot_service import Slot

CANCEL_TEXT = "Отменить"
CONFIRM_TEXT = "Отправить заявку"
BACK_TO_MENU_TEXT = "В меню"


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


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Можно отменить создание заявки",
    )


def dates_keyboard(dates: list[date]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=day.strftime("%d.%m.%Y"))] for day in dates]
    rows.append([KeyboardButton(text=CANCEL_TEXT)])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите дату",
    )


def durations_keyboard(durations: tuple[int, ...]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=f"{duration} минут")] for duration in durations]
    rows.append([KeyboardButton(text=CANCEL_TEXT)])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите длительность",
    )


def slots_keyboard(slots: list[Slot]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=slot.start.strftime("%H:%M"))] for slot in slots]
    rows.append([KeyboardButton(text=CANCEL_TEXT)])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите время",
    )


def confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CONFIRM_TEXT)],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Подтвердите заявку",
    )
