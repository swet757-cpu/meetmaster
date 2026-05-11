from datetime import date, datetime, timedelta

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot.keyboards import (
    APPROVE_ACTION,
    CANCEL_ACTION,
    CANCEL_ALIASES,
    DECLINE_ACTION,
    RESCHEDULE_ACTION,
    admin_active_meeting_actions_keyboard,
    admin_menu,
    admin_request_actions_keyboard,
    cancel_keyboard,
    dates_keyboard,
    slots_keyboard,
)
from app.bot.messages import ADMIN_ONLY
from app.bot.states import AdminRescheduleFlow
from app.config.settings import Settings
from app.db.models import RequestStatus
from app.db.repositories import (
    BookingRequestRepository,
    ClosedDayRepository,
    MeetingRepository,
    UserRepository,
)
from app.db.session import session_scope
from app.integrations.google_calendar import (
    CalendarEventDraft,
    GoogleCalendarClient,
    GoogleCalendarError,
)
from app.services.slot_service import (
    TimeInterval,
    available_booking_dates,
    booking_settings_from_app_settings,
    generate_slots,
)

router = Router()


def _is_admin(telegram_id: int, settings: Settings) -> bool:
    return telegram_id in settings.admin_telegram_ids


@router.message(Command("admin"))
async def admin(message: Message, settings: Settings) -> None:
    if not message.from_user or not _is_admin(message.from_user.id, settings):
        await message.answer(ADMIN_ONLY)
        return

    await message.answer("Админ-меню MeetMaster.", reply_markup=admin_menu())


@router.message(Command("admin_requests"))
@router.message(lambda message: message.text == "Заявки на согласовании")
async def pending_requests(
    message: Message,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not message.from_user or not _is_admin(message.from_user.id, settings):
        await message.answer(ADMIN_ONLY)
        return

    async with session_scope(session_factory) as session:
        requests = await BookingRequestRepository(session).list_pending()

    if not requests:
        await message.answer("Заявок на согласовании нет.", reply_markup=admin_menu())
        return

    await message.answer("Заявки на согласовании:", reply_markup=admin_menu())
    for request in requests[:10]:
        await message.answer(
            _admin_request_message(request),
            reply_markup=admin_request_actions_keyboard(request.id),
        )


@router.message(Command("admin_active"))
@router.message(lambda message: message.text == "Активные встречи")
async def active_meetings(
    message: Message,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not message.from_user or not _is_admin(message.from_user.id, settings):
        await message.answer(ADMIN_ONLY)
        return

    async with session_scope(session_factory) as session:
        requests = await BookingRequestRepository(session).list_active()

    if not requests:
        await message.answer("Активных встреч нет.", reply_markup=admin_menu())
        return

    await message.answer("Активные встречи:", reply_markup=admin_menu())
    for request in requests[:10]:
        await message.answer(
            _admin_request_message(request),
            reply_markup=admin_active_meeting_actions_keyboard(request.id),
        )


@router.callback_query(lambda query: bool(query.data and query.data.startswith("request:")))
async def handle_request_action(
    query: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not query.from_user or not _is_admin(query.from_user.id, settings):
        await query.answer(ADMIN_ONLY, show_alert=True)
        return

    action, request_id = _parse_request_callback(query.data or "")
    if action is None or request_id is None:
        await query.answer("Не удалось обработать действие.", show_alert=True)
        return

    if action == RESCHEDULE_ACTION:
        async with session_scope(session_factory) as session:
            request = await BookingRequestRepository(session).get_by_id(request_id)
            closed_days = await ClosedDayRepository(session).list_all()

        if request is None:
            await query.answer("Заявка не найдена.", show_alert=True)
            return

        if request.status not in {
            RequestStatus.PENDING_APPROVAL.value,
            RequestStatus.APPROVED.value,
            RequestStatus.RESCHEDULED.value,
        }:
            await query.answer("Эту заявку уже нельзя перенести.", show_alert=True)
            return

        booking_settings = booking_settings_from_app_settings(settings)
        dates = available_booking_dates(
            now=datetime.now(),
            closed_dates={item.day for item in closed_days},
            settings=booking_settings,
        )
        if not dates:
            await query.answer("Нет доступных дат для переноса.", show_alert=True)
            return

        await state.set_state(AdminRescheduleFlow.choosing_date)
        await state.update_data(request_id=request_id, duration=request.duration_minutes)
        if query.message:
            await query.message.answer(
                f"Выберите новую дату для заявки #{request_id}.",
                reply_markup=dates_keyboard(dates),
            )
        await query.answer("Выберите дату.")
        return

    status_by_action = {
        APPROVE_ACTION: RequestStatus.APPROVED,
        DECLINE_ACTION: RequestStatus.DECLINED,
        CANCEL_ACTION: RequestStatus.CANCELLED,
    }
    new_status = status_by_action.get(action)
    if new_status is None:
        await query.answer("Действие пока не поддерживается.", show_alert=True)
        return

    async with session_scope(session_factory) as session:
        request_repo = BookingRequestRepository(session)
        user_repo = UserRepository(session)
        meeting_repo = MeetingRepository(session)
        request = await request_repo.get_by_id(request_id)
        if request is None:
            await query.answer("Заявка не найдена.", show_alert=True)
            return

        allowed_statuses = {
            APPROVE_ACTION: {RequestStatus.PENDING_APPROVAL.value},
            DECLINE_ACTION: {RequestStatus.PENDING_APPROVAL.value},
            CANCEL_ACTION: {
                RequestStatus.PENDING_APPROVAL.value,
                RequestStatus.APPROVED.value,
                RequestStatus.RESCHEDULED.value,
            },
        }
        if request.status not in allowed_statuses[action]:
            await query.answer("Это действие недоступно для текущего статуса заявки.", show_alert=True)
            return

        meeting = await meeting_repo.get_by_booking_request_id(request.id)

        if settings.google_calendar_enabled and new_status == RequestStatus.APPROVED:
            try:
                event_id = await _create_google_event(settings, request)
            except GoogleCalendarError:
                await query.answer(
                    "Не удалось создать событие в Google Календаре. Заявка не изменена.",
                    show_alert=True,
                )
                return
            await meeting_repo.create_or_update(
                booking_request_id=request.id,
                google_calendar_event_id=event_id,
            )

        if settings.google_calendar_enabled and new_status == RequestStatus.CANCELLED and meeting is not None:
            try:
                await GoogleCalendarClient.from_settings(settings).delete_event(
                    meeting.google_calendar_event_id
                )
            except GoogleCalendarError:
                await query.answer(
                    "Не удалось отменить событие в Google Календаре. Заявка не изменена.",
                    show_alert=True,
                )
                return
            await meeting_repo.mark_cancelled(meeting)

        await request_repo.change_status(
            request=request,
            new_status=new_status,
            comment=f"Администратор выполнил действие: {action}.",
        )
        user = await user_repo.get_by_id(request.user_id)

    if user is not None:
        await bot.send_message(
            user.telegram_id,
            _user_status_message(
                new_status,
                request.start_at,
                google_synced=settings.google_calendar_enabled,
            ),
        )

    if query.message:
        await query.message.edit_text(
            f"{query.message.text}\n\nСтатус изменен: {_status_label(new_status)}"
        )
    await query.answer("Готово.")


@router.message(AdminRescheduleFlow.choosing_date)
async def choose_reschedule_date(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not message.from_user or not _is_admin(message.from_user.id, settings):
        await message.answer(ADMIN_ONLY)
        await state.clear()
        return

    if message.text in CANCEL_ALIASES:
        await state.clear()
        await message.answer("Перенос заявки отменен.", reply_markup=admin_menu())
        return

    selected_date = _parse_date(message.text or "")
    if selected_date is None:
        await message.answer("Выберите дату кнопкой из списка.", reply_markup=cancel_keyboard())
        return

    data = await state.get_data()
    request_id = int(data["request_id"])
    duration = int(data["duration"])
    async with session_scope(session_factory) as session:
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
        settings=booking_settings_from_app_settings(settings),
    )
    if not slots:
        await message.answer("На выбранную дату нет свободных слотов. Выберите другую дату.")
        return

    await state.update_data(date=selected_date.isoformat())
    await state.set_state(AdminRescheduleFlow.choosing_slot)
    await message.answer("Выберите новое время.", reply_markup=slots_keyboard(slots))


@router.message(AdminRescheduleFlow.choosing_slot)
async def choose_reschedule_slot(
    message: Message,
    state: FSMContext,
    bot: Bot,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not message.from_user or not _is_admin(message.from_user.id, settings):
        await message.answer(ADMIN_ONLY)
        await state.clear()
        return

    if message.text in CANCEL_ALIASES:
        await state.clear()
        await message.answer("Перенос заявки отменен.", reply_markup=admin_menu())
        return

    selected_time = _parse_time(message.text or "")
    if selected_time is None:
        await message.answer("Выберите время кнопкой из списка.", reply_markup=cancel_keyboard())
        return

    data = await state.get_data()
    request_id = int(data["request_id"])
    duration = int(data["duration"])
    selected_date = date.fromisoformat(data["date"])
    start_at = datetime.combine(selected_date, selected_time)
    end_at = start_at + timedelta(minutes=duration)

    async with session_scope(session_factory) as session:
        request_repo = BookingRequestRepository(session)
        user_repo = UserRepository(session)
        meeting_repo = MeetingRepository(session)
        request = await request_repo.get_by_id(request_id)
        if request is None:
            await message.answer("Заявка не найдена.", reply_markup=admin_menu())
            await state.clear()
            return

        blocking_requests = await request_repo.list_blocking_for_day(selected_date)
        slots = generate_slots(
            target_date=selected_date,
            duration_minutes=duration,
            now=datetime.now(),
            blocked_intervals=[
                TimeInterval(start=item.start_at, end=item.end_at)
                for item in blocking_requests
                if item.id != request_id
            ],
            settings=booking_settings_from_app_settings(settings),
        )
        if start_at not in {slot.start for slot in slots}:
            await message.answer("Это время уже недоступно. Выберите другой слот.", reply_markup=slots_keyboard(slots))
            return

        meeting = await meeting_repo.get_by_booking_request_id(request.id)
        if settings.google_calendar_enabled:
            draft = _google_event_draft(request, start_at, end_at)
            try:
                if meeting is None or meeting.status != "active":
                    event_id = await GoogleCalendarClient.from_settings(settings).create_event(draft)
                    await meeting_repo.create_or_update(
                        booking_request_id=request.id,
                        google_calendar_event_id=event_id,
                    )
                else:
                    await GoogleCalendarClient.from_settings(settings).update_event(
                        meeting.google_calendar_event_id,
                        draft,
                    )
            except GoogleCalendarError:
                await message.answer(
                    "Не удалось обновить Google Календарь. Перенос не сохранен.",
                    reply_markup=admin_menu(),
                )
                await state.clear()
                return

        await request_repo.reschedule(
            request=request,
            start_at=start_at,
            end_at=end_at,
            comment="Администратор перенес встречу.",
        )
        user = await user_repo.get_by_id(request.user_id)

    await state.clear()
    if user is not None:
        await bot.send_message(
            user.telegram_id,
            _user_status_message(
                RequestStatus.RESCHEDULED,
                start_at,
                google_synced=settings.google_calendar_enabled,
            ),
        )

    await message.answer(
        f"Заявка #{request_id} перенесена на {start_at.strftime('%d.%m.%Y %H:%M')}.",
        reply_markup=admin_menu(),
    )


def _parse_request_callback(data: str) -> tuple[str | None, int | None]:
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "request":
        return None, None
    try:
        return parts[1], int(parts[2])
    except ValueError:
        return None, None


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


def _parse_time(value: str):
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError:
        return None


def _status_label(status: RequestStatus) -> str:
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


async def _create_google_event(settings: Settings, request) -> str:
    busy_intervals = await GoogleCalendarClient.from_settings(settings).list_busy_intervals(
        request.start_at,
        request.end_at,
    )
    if busy_intervals:
        raise GoogleCalendarError("Google Calendar slot is busy.")

    return await GoogleCalendarClient.from_settings(settings).create_event(
        _google_event_draft(request, request.start_at, request.end_at)
    )


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


def _user_status_message(status: RequestStatus, start_at, google_synced: bool = False) -> str:
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
