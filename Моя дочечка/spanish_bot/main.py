from __future__ import annotations

import os

import telebot
from telebot import types

from database import get_next_word_for_review, get_stats, init_db, update_progress


TOKEN_ENV_NAME = "TELEGRAM_BOT_TOKEN"
CALLBACK_REMEMBERED = "remembered"
CALLBACK_FORGOT = "forgot"


def create_bot() -> telebot.TeleBot:
    token = os.getenv(TOKEN_ENV_NAME)
    if not token:
        raise RuntimeError(
            f"Не найдена переменная окружения {TOKEN_ENV_NAME}. "
            "Укажите токен бота перед запуском."
        )

    return telebot.TeleBot(token)


bot = create_bot()


@bot.message_handler(commands=["start"])
def handle_start(message: types.Message) -> None:
    init_db()
    text = (
        "Привет! Я бот для повторения испанских слов.\n\n"
        "Команды:\n"
        "/study - показать слово для повторения\n"
        "/stats - статистика"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["study"])
def handle_study(message: types.Message) -> None:
    init_db()
    send_next_card(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["stats"])
def handle_stats(message: types.Message) -> None:
    init_db()
    stats = get_stats(message.from_user.id)
    text = (
        "Статистика:\n"
        f"Всего слов: {stats['total']}\n"
        f"К повторению сейчас: {stats['due']}\n"
        f"На интервале 30 дней: {stats['learned']}"
    )
    bot.send_message(message.chat.id, text)


@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("review:"))
def handle_review_callback(call: types.CallbackQuery) -> None:
    init_db()

    try:
        _, action, word_id_raw = call.data.split(":")
        word_id = int(word_id_raw)
    except (ValueError, AttributeError):
        bot.answer_callback_query(call.id, "Не удалось обработать ответ.")
        return

    remembered = action == CALLBACK_REMEMBERED
    new_interval = update_progress(call.from_user.id, word_id, remembered)

    if remembered:
        result_text = f"Отлично. Следующий показ через {new_interval} дн."
    else:
        result_text = "Слово вернулось в очередь на повторение."

    bot.answer_callback_query(call.id, result_text)

    if call.message:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None,
        )
        bot.send_message(call.message.chat.id, result_text)
        send_next_card(call.message.chat.id, call.from_user.id)


def send_next_card(chat_id: int, user_id: int) -> None:
    word = get_next_word_for_review(user_id)
    if not word:
        bot.send_message(chat_id, "На сегодня слов для повторения нет. Возвращайся позже.")
        return

    text = (
        f"🇪🇸 {word['word']}\n"
        f"Перевод: {word['translation']}\n\n"
        f"Ассоциация: {word['association']}\n"
        f"Контекст: {word['example']}\n\n"
        f"Текущий интервал: {word['interval']} дн."
    )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            "Помню",
            callback_data=f"review:{CALLBACK_REMEMBERED}:{word['id']}",
        ),
        types.InlineKeyboardButton(
            "Забыл",
            callback_data=f"review:{CALLBACK_FORGOT}:{word['id']}",
        ),
    )
    bot.send_message(chat_id, text, reply_markup=keyboard)


if __name__ == "__main__":
    init_db()
    print("Бот запущен. Для остановки нажмите Ctrl+C.")
    bot.infinity_polling(skip_pending=True)
