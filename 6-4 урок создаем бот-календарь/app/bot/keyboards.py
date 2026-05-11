from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.services.slot_service import Slot

BOOK_TEXT = "Новая встреча"
MY_REQUESTS_TEXT = "Мои встречи"
HELP_TEXT = "Помощь"
CANCEL_TEXT = "Отмена"
CONFIRM_TEXT = "Отправить заявку"
APPROVE_ACTION = "approve"
DECLINE_ACTION = "decline"
CANCEL_ACTION = "cancel"
RESCHEDULE_ACTION = "reschedule"

BOOK_ALIASES = {BOOK_TEXT, "Записаться на встречу", "/book"}
MY_REQUESTS_ALIASES = {MY_REQUESTS_TEXT, "Мои заявки", "/requests"}
HELP_ALIASES = {HELP_TEXT, "/help"}
CANCEL_ALIASES = {CANCEL_TEXT, "Отменить"}


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BOOK_TEXT)],
            [KeyboardButton(text=MY_REQUESTS_TEXT), KeyboardButton(text=HELP_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Заявки на согласовании")],
            [KeyboardButton(text="Активные встречи")],
            [KeyboardButton(text="Настройки"), KeyboardButton(text="Статистика")],
            [KeyboardButton(text="Закрыть день"), KeyboardButton(text="Открыть день")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Админ-меню",
    )


def admin_active_meeting_actions_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перенести",
                    callback_data=f"request:{RESCHEDULE_ACTION}:{request_id}",
                ),
                InlineKeyboardButton(
                    text="Отменить",
                    callback_data=f"request:{CANCEL_ACTION}:{request_id}",
                ),
            ],
        ]
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Можно отменить",
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


def admin_request_actions_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтвердить",
                    callback_data=f"request:{APPROVE_ACTION}:{request_id}",
                ),
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=f"request:{DECLINE_ACTION}:{request_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Отменить",
                    callback_data=f"request:{CANCEL_ACTION}:{request_id}",
                ),
                InlineKeyboardButton(
                    text="Перенести",
                    callback_data=f"request:{RESCHEDULE_ACTION}:{request_id}",
                ),
            ],
        ]
    )
