import asyncio
from datetime import date, datetime
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import Settings, load_settings
from app.db.repositories import BookingRequestRepository, ClosedDayRepository, UserRepository
from app.db.session import create_app_session_factory, session_scope
from app.services.email_validator import is_valid_email
from app.services.slot_service import (
    TimeInterval,
    available_booking_dates,
    booking_settings_from_app_settings,
    generate_slots,
)

BOOK_TEXT = "Новая встреча"
MY_REQUESTS_TEXT = "Мои встречи"
HELP_TEXT = "Помощь"
CANCEL_TEXT = "Отмена"
CONFIRM_TEXT = "Отправить заявку"

BOOK_ALIASES = {BOOK_TEXT, "Записаться на встречу", "/book"}
MY_REQUESTS_ALIASES = {MY_REQUESTS_TEXT, "Мои заявки", "/requests"}
HELP_ALIASES = {HELP_TEXT, "/help"}
CANCEL_ALIASES = {CANCEL_TEXT, "Отменить"}

MAIN_MENU = [[BOOK_TEXT], [MY_REQUESTS_TEXT, HELP_TEXT]]
CANCEL_MENU = [[CANCEL_TEXT]]
CONFIRM_MENU = [[CONFIRM_TEXT], [CANCEL_TEXT]]


class TelegramApi:
    def __init__(self, token: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"

    def request(self, method: str, payload: dict | None = None, timeout: int = 35) -> dict:
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            f"{self.base_url}/{method}",
            data=data,
            headers=headers,
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def send_message(
        self,
        chat_id: int,
        text: str,
        keyboard: list[list[str]] | None = None,
    ) -> None:
        payload: dict = {"chat_id": chat_id, "text": text}
        if keyboard is not None:
            payload["reply_markup"] = {
                "keyboard": [[{"text": item} for item in row] for row in keyboard],
                "resize_keyboard": True,
            }
        self.request("sendMessage", payload, timeout=20)

    def get_updates(self, offset: int | None) -> list[dict]:
        payload = {"timeout": 25}
        if offset is not None:
            payload["offset"] = offset
        response = self.request("getUpdates", payload, timeout=35)
        return response.get("result", [])

    def set_commands(self) -> None:
        self.request(
            "setMyCommands",
            {
                "commands": [
                    {"command": "start", "description": "Главное меню"},
                    {"command": "book", "description": "Новая встреча"},
                    {"command": "requests", "description": "Мои встречи"},
                    {"command": "help", "description": "Помощь"},
                    {"command": "my_id", "description": "Мой Telegram ID"},
                ]
            },
            timeout=20,
        )


class LocalTestBot:
    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.telegram = TelegramApi(settings.bot_token)
        self.states: dict[int, dict] = {}

    def run(self) -> None:
        me = self.telegram.request("getMe").get("result", {})
        self.telegram.set_commands()
        print(f"LOCAL_TEST_BOT_OK=True username={me.get('username')}")
        offset: int | None = None
        while True:
            try:
                updates = self.telegram.get_updates(offset)
            except (urllib.error.URLError, TimeoutError) as exc:
                print(f"Telegram network retry: {type(exc).__name__}")
                time.sleep(3)
                continue

            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message")
                if message:
                    asyncio.run(self.handle_message(message))

    async def handle_message(self, message: dict) -> None:
        chat_id = message["chat"]["id"]
        user = message.get("from", {})
        user_id = user.get("id")
        text = (message.get("text") or "").strip()

        if text in {"/start", "В меню"}:
            self.states.pop(chat_id, None)
            self.telegram.send_message(
                chat_id,
                (
                    "Здравствуйте! Я MeetMaster.\n\n"
                    "Выберите действие кнопкой внизу или используйте меню команд."
                ),
                MAIN_MENU,
            )
            return

        if text == "/my_id":
            self.telegram.send_message(chat_id, f"Ваш Telegram ID: {user_id}", MAIN_MENU)
            return

        if text in CANCEL_ALIASES:
            self.states.pop(chat_id, None)
            self.telegram.send_message(chat_id, "Создание заявки отменено.", MAIN_MENU)
            return

        if text in HELP_ALIASES:
            self.telegram.send_message(chat_id, "Связаться с администратором.", MAIN_MENU)
            return

        if text in MY_REQUESTS_ALIASES:
            await self.show_my_requests(chat_id, user_id)
            return

        state = self.states.get(chat_id, {})
        step = state.get("step")

        if text in BOOK_ALIASES:
            await self.start_booking(chat_id)
        elif step == "date":
            await self.choose_date(chat_id, text)
        elif step == "duration":
            await self.choose_duration(chat_id, text)
        elif step == "slot":
            await self.choose_slot(chat_id, text)
        elif step == "email":
            await self.enter_email(chat_id, text)
        elif step == "description":
            await self.enter_description(chat_id, text)
        elif step == "confirm":
            await self.confirm(chat_id, user, text)
        else:
            self.telegram.send_message(chat_id, "Выберите действие кнопкой.", MAIN_MENU)

    async def start_booking(self, chat_id: int) -> None:
        booking_settings = booking_settings_from_app_settings(self.settings)
        async with session_scope(self.session_factory) as session:
            closed_days = await ClosedDayRepository(session).list_all()

        dates = available_booking_dates(
            now=datetime.now(),
            closed_dates={item.day for item in closed_days},
            settings=booking_settings,
        )
        self.states[chat_id] = {"step": "date"}
        self.telegram.send_message(
            chat_id,
            "Выберите дату встречи.",
            [[item.strftime("%d.%m.%Y")] for item in dates] + CANCEL_MENU,
        )

    async def choose_date(self, chat_id: int, text: str) -> None:
        selected_date = _parse_date(text)
        if selected_date is None:
            self.telegram.send_message(chat_id, "Выберите дату кнопкой из списка.", CANCEL_MENU)
            return

        self.states[chat_id] = {"step": "duration", "date": selected_date.isoformat()}
        durations = self.settings.allowed_durations
        self.telegram.send_message(
            chat_id,
            "Выберите длительность встречи.",
            [[f"{duration} минут"] for duration in durations] + CANCEL_MENU,
        )

    async def choose_duration(self, chat_id: int, text: str) -> None:
        duration = _parse_duration(text)
        if duration not in self.settings.allowed_durations:
            self.telegram.send_message(chat_id, "Выберите длительность кнопкой.", CANCEL_MENU)
            return

        state = self.states[chat_id]
        selected_date = date.fromisoformat(state["date"])
        async with session_scope(self.session_factory) as session:
            blocking_requests = await BookingRequestRepository(session).list_blocking_for_day(selected_date)

        slots = generate_slots(
            target_date=selected_date,
            duration_minutes=duration,
            now=datetime.now(),
            blocked_intervals=[
                TimeInterval(start=request.start_at, end=request.end_at)
                for request in blocking_requests
            ],
            settings=booking_settings_from_app_settings(self.settings),
        )
        if not slots:
            self.states.pop(chat_id, None)
            self.telegram.send_message(chat_id, "На выбранную дату нет свободных слотов.", MAIN_MENU)
            return

        state["step"] = "slot"
        state["duration"] = duration
        state["slots"] = {slot.start.strftime("%H:%M"): slot for slot in slots}
        self.telegram.send_message(
            chat_id,
            "Выберите свободное время.",
            [[slot.start.strftime("%H:%M")] for slot in slots] + CANCEL_MENU,
        )

    async def choose_slot(self, chat_id: int, text: str) -> None:
        state = self.states[chat_id]
        slot = state.get("slots", {}).get(text)
        if slot is None:
            self.telegram.send_message(chat_id, "Выберите время кнопкой из списка.", CANCEL_MENU)
            return

        state["step"] = "email"
        state["start_at"] = slot.start.isoformat()
        state["end_at"] = slot.end.isoformat()
        state.pop("slots", None)
        self.telegram.send_message(chat_id, "Введите email участника встречи.", CANCEL_MENU)

    async def enter_email(self, chat_id: int, text: str) -> None:
        if not is_valid_email(text):
            self.telegram.send_message(chat_id, "Email выглядит некорректно. Введите email еще раз.", CANCEL_MENU)
            return

        self.states[chat_id]["step"] = "description"
        self.states[chat_id]["email"] = text
        self.telegram.send_message(chat_id, "Введите тему или краткое описание встречи.", CANCEL_MENU)

    async def enter_description(self, chat_id: int, text: str) -> None:
        if not text:
            self.telegram.send_message(chat_id, "Описание не должно быть пустым.", CANCEL_MENU)
            return

        state = self.states[chat_id]
        state["step"] = "confirm"
        state["description"] = text
        start_at = datetime.fromisoformat(state["start_at"])
        summary = (
            "Проверьте заявку:\n\n"
            f"Дата: {start_at.strftime('%d.%m.%Y')}\n"
            f"Время: {start_at.strftime('%H:%M')}\n"
            f"Длительность: {state['duration']} минут\n"
            f"Email: {state['email']}\n"
            f"Описание: {text}\n\n"
            "Если все верно, отправьте заявку на согласование."
        )
        self.telegram.send_message(chat_id, summary, CONFIRM_MENU)

    async def confirm(self, chat_id: int, user: dict, text: str) -> None:
        if text != CONFIRM_TEXT:
            self.telegram.send_message(chat_id, "Подтвердите заявку кнопкой.", CONFIRM_MENU)
            return

        state = self.states[chat_id]
        start_at = datetime.fromisoformat(state["start_at"])
        end_at = datetime.fromisoformat(state["end_at"])
        async with session_scope(self.session_factory) as session:
            stored_user = await UserRepository(session).upsert_from_telegram(
                telegram_id=user["id"],
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
                username=user.get("username"),
                email=state["email"],
            )
            request = await BookingRequestRepository(session).create_pending(
                user_id=stored_user.id,
                start_at=start_at,
                end_at=end_at,
                duration_minutes=state["duration"],
                email=state["email"],
                description=state["description"],
            )

        self.states.pop(chat_id, None)
        self.telegram.send_message(
            chat_id,
            "Заявка отправлена на согласование. После решения администратора вы получите уведомление.",
            MAIN_MENU,
        )
        self.notify_admins(request.id, start_at, state)

    async def show_my_requests(self, chat_id: int, user_id: int) -> None:
        async with session_scope(self.session_factory) as session:
            user = await UserRepository(session).get_by_telegram_id(user_id)
            if user is None:
                self.telegram.send_message(chat_id, "У вас пока нет заявок.", MAIN_MENU)
                return
            requests = await BookingRequestRepository(session).list_by_user(user.id)

        if not requests:
            self.telegram.send_message(chat_id, "У вас пока нет заявок.", MAIN_MENU)
            return

        lines = ["Ваши заявки:"]
        for request in requests[:10]:
            lines.append(
                f"#{request.id}: {request.start_at.strftime('%d.%m.%Y %H:%M')}, "
                f"{request.duration_minutes} минут, статус: {request.status}"
            )
        self.telegram.send_message(chat_id, "\n".join(lines), MAIN_MENU)

    def notify_admins(self, request_id: int, start_at: datetime, state: dict) -> None:
        text = (
            "Новая заявка на встречу:\n\n"
            f"Заявка: #{request_id}\n"
            f"Дата: {start_at.strftime('%d.%m.%Y')}\n"
            f"Время: {start_at.strftime('%H:%M')}\n"
            f"Длительность: {state['duration']} минут\n"
            f"Email: {state['email']}\n"
            f"Описание: {state['description']}\n\n"
            "Подтверждение добавим следующим этапом."
        )
        for admin_id in self.settings.admin_telegram_ids:
            self.telegram.send_message(admin_id, text)


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


def _parse_duration(value: str) -> int | None:
    try:
        return int(value.replace("минут", "").strip())
    except ValueError:
        return None


def main() -> None:
    settings = load_settings()
    bot = LocalTestBot(settings=settings, session_factory=create_app_session_factory(settings))
    bot.run()


if __name__ == "__main__":
    main()
