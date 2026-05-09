from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


AUDIT_MODE = "Аудитор"
AUTOCORRECT_MODE = "Авто-корректор"
CANCEL = "Отмена"


mode_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=AUDIT_MODE), KeyboardButton(text=AUTOCORRECT_MODE)],
        [KeyboardButton(text=CANCEL)],
    ],
    resize_keyboard=True,
)
