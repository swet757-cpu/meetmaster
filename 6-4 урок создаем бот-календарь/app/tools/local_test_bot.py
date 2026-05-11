import asyncio
from datetime import date, datetime
import json
from pathlib import Path
import time
import traceback
import urllib.error
import urllib.request

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import Settings, load_settings
from app.db.models import RequestStatus
from app.db.repositories import (
    BookingRequestRepository,
    ClosedDayRepository,
    MeetingRepository,
    UserRepository,
)
from app.db.session import create_app_session_factory, session_scope
from app.integrations.google_calendar import (
    CalendarEventDraft,
    GoogleCalendarClient,
    GoogleCalendarError,
)
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
ADMIN_REQUESTS_TEXT = "Заявки на согласовании"
ACTIVE_MEETINGS_TEXT = "Активные встречи"
RESCHEDULE_ACTION = "reschedule"

BOOK_ALIASES = {BOOK_TEXT, "Записаться на встречу", "/book"}
MY_REQUESTS_ALIASES = {MY_REQUESTS_TEXT, "Мои заявки", "/requests"}
HELP_ALIASES = {HELP_TEXT, "/help"}
CANCEL_ALIASES = {CANCEL_TEXT, "Отменить"}
ADMIN_REQUESTS_ALIASES = {ADMIN_REQUESTS_TEXT, "/admin_requests"}
ACTIVE_MEETINGS_ALIASES = {ACTIVE_MEETINGS_TEXT, "/admin_active"}

MAIN_MENU = [[BOOK_TEXT], [MY_REQUESTS_TEXT, HELP_TEXT]]
ADMIN_MENU = [[ADMIN_REQUESTS_TEXT], [ACTIVE_MEETINGS_TEXT]]
CANCEL_MENU = [[CANCEL_TEXT]]
CONFIRM_MENU = [[CONFIRM_TEXT], [CANCEL_TEXT]]
LOG_PATH = Path("local_data/local_test_bot_internal.log")


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
        inline_keyboard: list[list[dict]] | None = None,
    ) -> None:
        payload: dict = {"chat_id": chat_id, "text": text}
        if inline_keyboard is not None:
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}
        elif keyboard is not None:
            payload["reply_markup"] = {
                "keyboard": [[{"text": item} for item in row] for row in keyboard],
                "resize_keyboard": True,
            }
        self.request("sendMessage", payload, timeout=20)

    def edit_message_text(self, chat_id: int, message_id: int, text: str) -> None:
        self.request(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
            },
            timeout=20,
        )

    def answer_callback_query(self, callback_query_id: str, text: str) -> None:
        self.request(
            "answerCallbackQuery",
            {
                "callback_query_id": callback_query_id,
                "text": text,
            },
            timeout=20,
        )

    def get_updates(self, offset: int | None) -> list[dict]:
        payload = {"timeout": 25}
        if offset is not None:
            payload["offset"] = offset
        response = self.request("getUpdates", payload, timeout=35)
        return response.get("result", [])

    def drop_pending_updates(self) -> int | None:
        response = self.request("getUpdates", {"offset": -1, "timeout": 1}, timeout=10)
        updates = response.get("result", [])
        if not updates:
            return None
        return updates[-1]["update_id"] + 1

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
                    {"command": "admin", "description": "Админ-меню"},
                    {"command": "admin_requests", "description": "Заявки на согласовании"},
                    {"command": "admin_active", "description": "Активные встречи"},
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
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _log("LOCAL_TEST_BOT_STARTING")
        try:
            me = self.telegram.request("getMe", timeout=10).get("result", {})
            _log(f"LOCAL_TEST_BOT_OK=True username={me.get('username')}")
        except Exception as exc:
            _log_exception("getMe failed", exc)

        try:
            self.telegram.set_commands()
        except Exception as exc:
            _log_exception("set commands failed", exc)

        try:
            offset = self.telegram.drop_pending_updates()
        except Exception as exc:
            _log_exception("drop pending updates failed", exc)
            offset = None
        _log(f"START_OFFSET={offset}")
        while True:
            try:
                updates = self.telegram.get_updates(offset)
            except (urllib.error.URLError, TimeoutError) as exc:
                _log(f"Telegram network retry: {type(exc).__name__}: {exc}")
                time.sleep(3)
                continue
            except Exception as exc:
                _log_exception("get_updates failed", exc)
                time.sleep(3)
                continue

            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message")
                if message:
                    try:
                        asyncio.run(self.handle_message(message))
                    except Exception as exc:
                        _log_exception("handle_message failed", exc)
                callback_query = update.get("callback_query")
                if callback_query:
                    try:
                        asyncio.run(self.handle_callback_query(callback_query))
                    except Exception as exc:
                        _log_exception("handle_callback_query failed", exc)

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

        if text == "/admin":
            if user_id not in self.settings.admin_telegram_ids:
                self.telegram.send_message(chat_id, "Это действие доступно только администратору.", MAIN_MENU)
                return
            self.telegram.send_message(chat_id, "Админ-меню MeetMaster.", ADMIN_MENU)
            return

        if text in ADMIN_REQUESTS_ALIASES:
            await self.show_pending_requests(chat_id, user_id)
            return

        if text in ACTIVE_MEETINGS_ALIASES:
            await self.show_active_meetings(chat_id, user_id)
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

        if step == "admin_reschedule_date":
            await self.choose_admin_reschedule_date(chat_id, user_id, text)
        elif step == "admin_reschedule_slot":
            await self.choose_admin_reschedule_slot(chat_id, user_id, text)
        elif text in BOOK_ALIASES:
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

    async def handle_callback_query(self, callback_query: dict) -> None:
        user = callback_query.get("from", {})
        if user.get("id") not in self.settings.admin_telegram_ids:
            self.telegram.answer_callback_query(callback_query["id"], "Это действие доступно только администратору.")
            return

        action, request_id = _parse_request_callback(callback_query.get("data", ""))
        if action is None or request_id is None:
            self.telegram.answer_callback_query(callback_query["id"], "Не удалось обработать действие.")
            return

        status_by_action = {
            "approve": RequestStatus.APPROVED,
            "decline": RequestStatus.DECLINED,
            "cancel": RequestStatus.CANCELLED,
        }
        new_status = status_by_action.get(action)
        if action == RESCHEDULE_ACTION:
            async with session_scope(self.session_factory) as session:
                request = await BookingRequestRepository(session).get_by_id(request_id)
                closed_days = await ClosedDayRepository(session).list_all()
            if request is None:
                self.telegram.answer_callback_query(callback_query["id"], "Заявка не найдена.")
                return
            if request.status not in {
                RequestStatus.PENDING_APPROVAL.value,
                RequestStatus.APPROVED.value,
                RequestStatus.RESCHEDULED.value,
            }:
                self.telegram.answer_callback_query(callback_query["id"], "Эту заявку уже нельзя перенести.")
                return

            dates = available_booking_dates(
                now=datetime.now(),
                closed_dates={item.day for item in closed_days},
                settings=booking_settings_from_app_settings(self.settings),
            )
            if not dates:
                self.telegram.answer_callback_query(callback_query["id"], "Нет доступных дат для переноса.")
                return

            chat_id = callback_query["message"]["chat"]["id"]
            self.states[chat_id] = {
                "step": "admin_reschedule_date",
                "request_id": request_id,
                "duration": request.duration_minutes,
            }
            self.telegram.send_message(
                chat_id,
                f"Выберите новую дату для заявки #{request_id}.",
                [[item.strftime("%d.%m.%Y")] for item in dates] + CANCEL_MENU,
            )
            self.telegram.answer_callback_query(callback_query["id"], "Выберите дату.")
            return

        if new_status is None:
            self.telegram.answer_callback_query(callback_query["id"], "Действие пока не поддерживается.")
            return

        async with session_scope(self.session_factory) as session:
            request_repo = BookingRequestRepository(session)
            user_repo = UserRepository(session)
            meeting_repo = MeetingRepository(session)
            request = await request_repo.get_by_id(request_id)
            if request is None:
                self.telegram.answer_callback_query(callback_query["id"], "Заявка не найдена.")
                return
            allowed_statuses = {
                "approve": {RequestStatus.PENDING_APPROVAL.value},
                "decline": {RequestStatus.PENDING_APPROVAL.value},
                "cancel": {
                    RequestStatus.PENDING_APPROVAL.value,
                    RequestStatus.APPROVED.value,
                    RequestStatus.RESCHEDULED.value,
                },
            }
            if request.status not in allowed_statuses[action]:
                self.telegram.answer_callback_query(
                    callback_query["id"],
                    "Это действие недоступно для текущего статуса заявки.",
                )
                return

            meeting = await meeting_repo.get_by_booking_request_id(request.id)
            if self.settings.google_calendar_enabled and new_status == RequestStatus.APPROVED:
                try:
                    event_id = await self.create_google_event(request)
                except GoogleCalendarError:
                    self.telegram.answer_callback_query(
                        callback_query["id"],
                        "Не удалось создать событие в Google Календаре.",
                    )
                    return
                await meeting_repo.create_or_update(
                    booking_request_id=request.id,
                    google_calendar_event_id=event_id,
                )

            if self.settings.google_calendar_enabled and new_status == RequestStatus.CANCELLED and meeting is not None:
                try:
                    await GoogleCalendarClient.from_settings(self.settings).delete_event(
                        meeting.google_calendar_event_id
                    )
                except GoogleCalendarError:
                    self.telegram.answer_callback_query(
                        callback_query["id"],
                        "Не удалось отменить событие в Google Календаре.",
                    )
                    return
                await meeting_repo.mark_cancelled(meeting)

            await request_repo.change_status(
                request=request,
                new_status=new_status,
                comment=f"Администратор выполнил действие: {action}.",
            )
            stored_user = await user_repo.get_by_id(request.user_id)

        if stored_user is not None:
            self.telegram.send_message(
                stored_user.telegram_id,
                _user_status_message(
                    new_status,
                    request.start_at,
                    google_synced=self.settings.google_calendar_enabled,
                ),
            )

        message = callback_query.get("message") or {}
        if message:
            self.telegram.edit_message_text(
                message["chat"]["id"],
                message["message_id"],
                f"{message.get('text', '')}\n\nСтатус изменен: {_status_label(new_status)}",
            )
        self.telegram.answer_callback_query(callback_query["id"], "Готово.")

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
                f"{request.duration_minutes} минут, статус: {_status_label(request.status)}"
            )
        self.telegram.send_message(chat_id, "\n".join(lines), MAIN_MENU)

    async def choose_admin_reschedule_date(self, chat_id: int, user_id: int, text: str) -> None:
        if user_id not in self.settings.admin_telegram_ids:
            self.states.pop(chat_id, None)
            self.telegram.send_message(chat_id, "Это действие доступно только администратору.", MAIN_MENU)
            return

        if text in CANCEL_ALIASES:
            self.states.pop(chat_id, None)
            self.telegram.send_message(chat_id, "Перенос заявки отменен.", ADMIN_MENU)
            return

        selected_date = _parse_date(text)
        if selected_date is None:
            self.telegram.send_message(chat_id, "Выберите дату кнопкой из списка.", CANCEL_MENU)
            return

        state = self.states[chat_id]
        request_id = int(state["request_id"])
        duration = int(state["duration"])
        async with session_scope(self.session_factory) as session:
            blocking_requests = await BookingRequestRepository(session).list_blocking_for_day(selected_date)

        slots = generate_slots(
            target_date=selected_date,
            duration_minutes=duration,
            now=datetime.now(),
            blocked_intervals=[
                TimeInterval(start=request.start_at, end=request.end_at)
                for request in blocking_requests
                if request.id != request_id
            ],
            settings=booking_settings_from_app_settings(self.settings),
        )
        if not slots:
            self.telegram.send_message(chat_id, "На выбранную дату нет свободных слотов. Выберите другую дату.")
            return

        state["step"] = "admin_reschedule_slot"
        state["date"] = selected_date.isoformat()
        state["slots"] = {slot.start.strftime("%H:%M"): slot for slot in slots}
        self.telegram.send_message(
            chat_id,
            "Выберите новое время.",
            [[slot.start.strftime("%H:%M")] for slot in slots] + CANCEL_MENU,
        )

    async def choose_admin_reschedule_slot(self, chat_id: int, user_id: int, text: str) -> None:
        if user_id not in self.settings.admin_telegram_ids:
            self.states.pop(chat_id, None)
            self.telegram.send_message(chat_id, "Это действие доступно только администратору.", MAIN_MENU)
            return

        if text in CANCEL_ALIASES:
            self.states.pop(chat_id, None)
            self.telegram.send_message(chat_id, "Перенос заявки отменен.", ADMIN_MENU)
            return

        state = self.states[chat_id]
        slot = state.get("slots", {}).get(text)
        if slot is None:
            self.telegram.send_message(chat_id, "Выберите время кнопкой из списка.", CANCEL_MENU)
            return

        request_id = int(state["request_id"])
        async with session_scope(self.session_factory) as session:
            request_repo = BookingRequestRepository(session)
            user_repo = UserRepository(session)
            meeting_repo = MeetingRepository(session)
            request = await request_repo.get_by_id(request_id)
            if request is None:
                self.states.pop(chat_id, None)
                self.telegram.send_message(chat_id, "Заявка не найдена.", ADMIN_MENU)
                return

            meeting = await meeting_repo.get_by_booking_request_id(request.id)
            if self.settings.google_calendar_enabled:
                draft = _google_event_draft(request, slot.start, slot.end)
                try:
                    if meeting is None or meeting.status != "active":
                        event_id = await GoogleCalendarClient.from_settings(self.settings).create_event(draft)
                        await meeting_repo.create_or_update(
                            booking_request_id=request.id,
                            google_calendar_event_id=event_id,
                        )
                    else:
                        await GoogleCalendarClient.from_settings(self.settings).update_event(
                            meeting.google_calendar_event_id,
                            draft,
                        )
                except GoogleCalendarError:
                    self.states.pop(chat_id, None)
                    self.telegram.send_message(
                        chat_id,
                        "Не удалось обновить Google Календарь. Перенос не сохранен.",
                        ADMIN_MENU,
                    )
                    return

            await request_repo.reschedule(
                request=request,
                start_at=slot.start,
                end_at=slot.end,
                comment="Администратор перенес встречу.",
            )
            stored_user = await user_repo.get_by_id(request.user_id)

        self.states.pop(chat_id, None)
        if stored_user is not None:
            self.telegram.send_message(
                stored_user.telegram_id,
                _user_status_message(
                    RequestStatus.RESCHEDULED,
                    slot.start,
                    google_synced=self.settings.google_calendar_enabled,
                ),
            )
        self.telegram.send_message(
            chat_id,
            f"Заявка #{request_id} перенесена на {slot.start.strftime('%d.%m.%Y %H:%M')}.",
            ADMIN_MENU,
        )

    async def show_pending_requests(self, chat_id: int, user_id: int) -> None:
        if user_id not in self.settings.admin_telegram_ids:
            self.telegram.send_message(chat_id, "Это действие доступно только администратору.", MAIN_MENU)
            return

        async with session_scope(self.session_factory) as session:
            requests = await BookingRequestRepository(session).list_pending()

        if not requests:
            self.telegram.send_message(chat_id, "Заявок на согласовании нет.", ADMIN_MENU)
            return

        self.telegram.send_message(chat_id, "Заявки на согласовании:", ADMIN_MENU)
        for request in requests[:10]:
            self.telegram.send_message(
                chat_id,
                _admin_request_message(request),
                inline_keyboard=_admin_request_actions_keyboard(request.id),
            )

    async def show_active_meetings(self, chat_id: int, user_id: int) -> None:
        if user_id not in self.settings.admin_telegram_ids:
            self.telegram.send_message(chat_id, "Это действие доступно только администратору.", MAIN_MENU)
            return

        async with session_scope(self.session_factory) as session:
            requests = await BookingRequestRepository(session).list_active()

        if not requests:
            self.telegram.send_message(chat_id, "Активных встреч нет.", ADMIN_MENU)
            return

        self.telegram.send_message(chat_id, "Активные встречи:", ADMIN_MENU)
        for request in requests[:10]:
            self.telegram.send_message(
                chat_id,
                _admin_request_message(request),
                inline_keyboard=_admin_active_meeting_actions_keyboard(request.id),
            )

    def notify_admins(self, request_id: int, start_at: datetime, state: dict) -> None:
        text = (
            "Новая заявка на встречу:\n\n"
            f"Заявка: #{request_id}\n"
            f"Дата: {start_at.strftime('%d.%m.%Y')}\n"
            f"Время: {start_at.strftime('%H:%M')}\n"
            f"Длительность: {state['duration']} минут\n"
            f"Email: {state['email']}\n"
            f"Описание: {state['description']}\n\n"
            "Выберите действие кнопкой ниже."
        )
        for admin_id in self.settings.admin_telegram_ids:
            try:
                self.telegram.send_message(
                    admin_id,
                    text,
                    inline_keyboard=_admin_request_actions_keyboard(request_id),
                )
                _log(f"ADMIN_NOTIFICATION_SENT request_id={request_id}")
            except Exception as exc:
                _log_exception(f"admin notification failed request_id={request_id}", exc)

    async def create_google_event(self, request) -> str:
        busy_intervals = await GoogleCalendarClient.from_settings(self.settings).list_busy_intervals(
            request.start_at,
            request.end_at,
        )
        if busy_intervals:
            raise GoogleCalendarError("Google Calendar slot is busy.")

        return await GoogleCalendarClient.from_settings(self.settings).create_event(
            _google_event_draft(request, request.start_at, request.end_at)
        )


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


def _parse_request_callback(data: str) -> tuple[str | None, int | None]:
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "request":
        return None, None
    try:
        return parts[1], int(parts[2])
    except ValueError:
        return None, None


def _admin_request_actions_keyboard(request_id: int) -> list[list[dict]]:
    return [
        [
            {"text": "Подтвердить", "callback_data": f"request:approve:{request_id}"},
            {"text": "Отклонить", "callback_data": f"request:decline:{request_id}"},
        ],
        [
            {"text": "Отменить", "callback_data": f"request:cancel:{request_id}"},
            {"text": "Перенести", "callback_data": f"request:{RESCHEDULE_ACTION}:{request_id}"},
        ],
    ]


def _admin_active_meeting_actions_keyboard(request_id: int) -> list[list[dict]]:
    return [
        [
            {"text": "Перенести", "callback_data": f"request:{RESCHEDULE_ACTION}:{request_id}"},
            {"text": "Отменить", "callback_data": f"request:cancel:{request_id}"},
        ],
    ]


def _status_label(status: RequestStatus | str) -> str:
    value = status.value if isinstance(status, RequestStatus) else status
    labels = {
        RequestStatus.PENDING_APPROVAL.value: "на согласовании",
        RequestStatus.APPROVED.value: "подтверждена",
        RequestStatus.DECLINED.value: "отклонена",
        RequestStatus.CANCELLED.value: "отменена",
        RequestStatus.RESCHEDULED.value: "перенесена",
    }
    return labels.get(value, value)


def _admin_request_message(request) -> str:
    return (
        "Заявка на встречу:\n\n"
        f"Заявка: #{request.id}\n"
        f"Дата: {request.start_at.strftime('%d.%m.%Y')}\n"
        f"Время: {request.start_at.strftime('%H:%M')}\n"
        f"Длительность: {request.duration_minutes} минут\n"
        f"Статус: {_status_label(request.status)}\n"
        f"Email: {request.email}\n"
        f"Описание: {request.description}"
    )


def _user_status_message(
    status: RequestStatus,
    start_at: datetime,
    google_synced: bool = False,
) -> str:
    if status == RequestStatus.APPROVED:
        calendar_text = (
            "Встреча добавлена в Google Календарь."
            if google_synced
            else "Добавление в Google Календарь будет подключено следующим этапом."
        )
        return (
            "Ваша заявка подтверждена.\n\n"
            f"Дата и время: {start_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"{calendar_text}"
        )
    if status == RequestStatus.DECLINED:
        return "Ваша заявка отклонена. Можно выбрать другой слот."
    if status == RequestStatus.CANCELLED:
        return "Ваша заявка отменена администратором."
    if status == RequestStatus.RESCHEDULED:
        calendar_text = (
            "Google Календарь обновлен."
            if google_synced
            else "Обновление Google Календаря будет подключено следующим этапом."
        )
        return (
            "Ваша встреча перенесена администратором.\n\n"
            f"Новая дата и время: {start_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"{calendar_text}"
        )
    return "Статус вашей заявки изменен."


def _google_event_draft(request, start_at: datetime, end_at: datetime) -> CalendarEventDraft:
    return CalendarEventDraft(
        title=request.description,
        description=(
            f"MeetMaster\n"
            f"Заявка: #{request.id}\n"
            f"Email участника: {request.email}"
        ),
        start_at=start_at,
        end_at=end_at,
        attendee_email=request.email,
    )


def _log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} {message}"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(line + "\n")
    try:
        print(line, flush=True)
    except Exception:
        pass


def _log_exception(context: str, exc: Exception) -> None:
    _log(f"{context}: {type(exc).__name__}: {exc}")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        traceback.print_exc(file=log_file)


def main() -> None:
    settings = load_settings()
    bot = LocalTestBot(settings=settings, session_factory=create_app_session_factory(settings))
    bot.run()


if __name__ == "__main__":
    main()
