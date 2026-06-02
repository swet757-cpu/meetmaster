from __future__ import annotations

import ctypes
import json
import logging
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from ctypes import wintypes
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "telegram_token.dpapi"
STATE_FILE = BASE_DIR / "state.json"
LOG_FILE = BASE_DIR / "bot.log"
MUTEX_NAME = "Local\\CashFlowLifesaverBot"

CHECKLIST_URL = (
    "https://drive.google.com/file/d/"
    "1Ui_lXPZqy6x7wiX__ASeZUCkHJqFt4Il/view?usp=drive_link"
)
PROFIT_GUIDE_URL = (
    "https://drive.google.com/file/d/"
    "1FH8axlGXvUMtMXyrCwgFtfPyNNs0UP8n/view?usp=drive_link"
)
CALENDAR_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1Udx77aRfCAn0kGeKyT95B_hPf3rDDleoH9-CfBIuwAU/edit?usp=sharing"
)


START_TEXT = """Привет! Я твой финансовый ассистент.

Помогу быстро разобраться с деньгами в бизнесе без сложных формул.

Выбери, что сейчас актуально:"""

EMERGENCY_TEXT = """Экстренный план при нехватке денег

1. Отложи платежи, которые не остановят бизнес прямо сейчас: дивиденды, закупки впрок и необязательные расходы.

2. Предложи клиентам-должникам скидку 3-5%, если они заплатят сегодня.

3. Договорись о переносе платежей заранее. Честный разговор с арендодателем или поставщиком лучше молчания.

Чек-лист «5 шагов при кассовом разрыве»:
{checklist}"""

PROFIT_TEXT = """Почему на счете нет денег, хотя есть прибыль?

Прибыль показывает финансовый результат, а деньги - остаток на счетах и в кассе.

Деньги часто находятся в трех местах:

1. Дебиторская задолженность: клиенты еще не оплатили отгрузки.
2. Запасы: деньги вложены в товар на складе.
3. Погашение кредитов: выплата тела кредита уменьшает деньги, но не расходы в отчете о прибылях и убытках.

Подробный гайд:
{guide}"""

CALENDAR_TEXT = """Платежный календарь

Внеси ожидаемые поступления и списания по дням. Если заранее увидишь отрицательный остаток, будет время перенести платеж, ускорить поступление или сократить расход.

Для начала планируй на 2 недели вперед. Затем переходи на горизонт в 1 месяц.

Шаблон:
{calendar}"""

CALENDAR_HOW_TO_TEXT = """Как заполнить платежный календарь

1. Укажи остаток денег на начало дня.
2. Внеси ожидаемые поступления по датам.
3. Внеси обязательные и плановые списания по датам.
4. Проверь остаток на конец каждого дня.
5. Если появляется минус, начни работать с ним заранее: ускорь оплату клиентов, перенеси необязательный расход или договорись о рассрочке."""

FAQ_TEXT = """Короткие ответы

На какой срок планировать?
Начни с 2 недель. Когда процесс станет привычным, переходи на 1 месяц.

Кто ведет календарь?
Тот, кто распоряжается деньгами. Собственник может начать сам, затем делегировать ведение и проверять остаток каждую неделю.

Что делать, если разрывы повторяются каждый месяц?
Проверь маржу, постоянные расходы, сроки оплаты клиентов и объем запасов. Регулярный кассовый разрыв - симптом системной проблемы."""


class DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def configure_logging() -> None:
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )


def ensure_single_instance() -> Any:
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not mutex:
        raise RuntimeError("Не удалось создать блокировку процесса.")
    if kernel32.GetLastError() == 183:
        kernel32.CloseHandle(mutex)
        raise RuntimeError("Бот уже запущен.")
    return mutex


def decrypt_for_current_user(path: Path) -> str:
    encrypted = path.read_bytes()
    encrypted_buffer = ctypes.create_string_buffer(encrypted)
    encrypted_blob = DataBlob(
        len(encrypted),
        ctypes.cast(encrypted_buffer, ctypes.POINTER(ctypes.c_char)),
    )
    decrypted_blob = DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(encrypted_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(decrypted_blob),
    ):
        raise RuntimeError("Не удалось расшифровать токен для текущего пользователя Windows.")
    try:
        decrypted = ctypes.string_at(decrypted_blob.pbData, decrypted_blob.cbData)
        return decrypted.decode("utf-8")
    finally:
        kernel32.LocalFree(decrypted_blob.pbData)


def load_offset() -> int:
    if not STATE_FILE.exists():
        return 0
    try:
        return int(json.loads(STATE_FILE.read_text(encoding="utf-8")).get("offset", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def save_offset(offset: int) -> None:
    STATE_FILE.write_text(
        json.dumps({"offset": offset}, ensure_ascii=False),
        encoding="utf-8",
    )


class TelegramBot:
    def __init__(self, token: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}/"

    def request(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        encoded = urllib.parse.urlencode(payload or {}).encode("utf-8")
        request = urllib.request.Request(self.base_url + method, data=encoded, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Telegram API вернул HTTP {error.code}.") from error
        except urllib.error.URLError as error:
            raise RuntimeError("Нет соединения с Telegram API.") from error
        if not result.get("ok"):
            description = result.get("description", "неизвестная ошибка")
            raise RuntimeError(f"Telegram API: {description}")
        return result.get("result")

    def send_message(
        self,
        chat_id: int,
        text: str,
        keyboard: list[list[dict[str, str]]] | None = None,
    ) -> None:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if keyboard:
            payload["reply_markup"] = json.dumps(
                {"inline_keyboard": keyboard},
                ensure_ascii=False,
            )
        self.request("sendMessage", payload)

    def answer_callback(self, callback_id: str) -> None:
        self.request("answerCallbackQuery", {"callback_query_id": callback_id})

    def delete_webhook(self) -> None:
        self.request("deleteWebhook", {"drop_pending_updates": "false"})


def main_keyboard() -> list[list[dict[str, str]]]:
    return [
        [{"text": "Кассовый разрыв", "callback_data": "emergency"}],
        [{"text": "Прибыль есть, а денег нет", "callback_data": "profit_vs_cash"}],
        [{"text": "Платежный календарь", "callback_data": "calendar"}],
        [{"text": "Короткие ответы", "callback_data": "faq"}],
    ]


def back_keyboard() -> list[list[dict[str, str]]]:
    return [[{"text": "В главное меню", "callback_data": "start"}]]


def calendar_keyboard() -> list[list[dict[str, str]]]:
    return [
        [{"text": "Как заполнить календарь", "callback_data": "calendar_how_to"}],
        [{"text": "В главное меню", "callback_data": "start"}],
    ]


def send_section(bot: TelegramBot, chat_id: int, section: str) -> None:
    if section == "start":
        bot.send_message(chat_id, START_TEXT, main_keyboard())
    elif section == "emergency":
        bot.send_message(chat_id, EMERGENCY_TEXT.format(checklist=CHECKLIST_URL), back_keyboard())
    elif section == "profit_vs_cash":
        bot.send_message(chat_id, PROFIT_TEXT.format(guide=PROFIT_GUIDE_URL), back_keyboard())
    elif section == "calendar":
        bot.send_message(chat_id, CALENDAR_TEXT.format(calendar=CALENDAR_URL), calendar_keyboard())
    elif section == "calendar_how_to":
        bot.send_message(chat_id, CALENDAR_HOW_TO_TEXT, back_keyboard())
    elif section == "faq":
        bot.send_message(chat_id, FAQ_TEXT, back_keyboard())
    else:
        bot.send_message(chat_id, "Выбери нужный раздел:", main_keyboard())


def detect_section(text: str) -> str:
    normalized = text.casefold()
    if text.startswith("/start") or "меню" in normalized:
        return "start"
    if any(word in normalized for word in ("кассов", "разрыв", "нехват", "срочно", "завтра")):
        return "emergency"
    if any(word in normalized for word in ("прибыл", "денег нет", "счет пуст", "счёт пуст")):
        return "profit_vs_cash"
    if any(word in normalized for word in ("календар", "планир", "платеж", "платёж")):
        return "calendar"
    if any(word in normalized for word in ("вопрос", "срок", "кто должен", "каждый месяц")):
        return "faq"
    return "unknown"


def handle_update(bot: TelegramBot, update: dict[str, Any]) -> None:
    callback = update.get("callback_query")
    if callback:
        bot.answer_callback(callback["id"])
        chat_id = callback["message"]["chat"]["id"]
        send_section(bot, chat_id, callback.get("data", "start"))
        return

    message = update.get("message") or update.get("edited_message")
    if not message:
        return
    chat_id = message["chat"]["id"]
    text = message.get("text")
    if text:
        send_section(bot, chat_id, detect_section(text))
        return
    bot.send_message(
        chat_id,
        "Сейчас я работаю в бесплатном режиме и понимаю текстовые сообщения. Напиши вопрос текстом.",
        main_keyboard(),
    )


def run() -> None:
    configure_logging()
    if sys.platform != "win32":
        raise RuntimeError("Локальная версия подготовлена для Windows.")
    ensure_single_instance()
    if not TOKEN_FILE.exists():
        raise RuntimeError("Сначала запустите setup_bot.ps1 и настройте токен Telegram.")

    bot = TelegramBot(decrypt_for_current_user(TOKEN_FILE))
    me = bot.request("getMe")
    logging.info("Бот запущен: @%s", me.get("username", "unknown"))
    bot.delete_webhook()
    offset = load_offset()

    while True:
        try:
            updates = bot.request(
                "getUpdates",
                {"offset": offset, "timeout": 25, "allowed_updates": '["message","callback_query"]'},
            )
            for update in updates:
                offset = int(update["update_id"]) + 1
                save_offset(offset)
                try:
                    handle_update(bot, update)
                except Exception:
                    logging.exception("Ошибка обработки сообщения.")
        except Exception:
            logging.exception("Ошибка соединения. Повтор через 10 секунд.")
            time.sleep(10)


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        configure_logging()
        logging.exception("Бот остановлен.")
        print(f"Ошибка: {error}", file=sys.stderr)
        raise SystemExit(1)
