from datetime import date, datetime, timedelta

from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot.keyboards import (
    CANCEL_TEXT,
    CONFIRM_TEXT,
    cancel_keyboard,
    confirm_keyboard,
    dates_keyboard,
    durations_keyboard,
    main_menu,
    slots_keyboard,
)
from app.bot.messages import HELP, UNKNOWN_ACTION, WELCOME
from app.bot.states import BookingFlow
from app.config.settings import Settings
from app.db.repositories import BookingRequestRepository, ClosedDayRepository, UserRepository
from app.db.session import session_scope
from app.services.email_validator import is_valid_email
from app.services.slot_service import (
    TimeInterval,
    available_booking_dates,
    booking_settings_from_app_settings,
    generate_slots,
)

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_menu())


@router.message(Command("my_id"))
async def my_telegram_id(message: Message) -> None:
    if not message.from_user:
        await message.answer("Не удалось определить Telegram ID.")
        return

    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")


@router.message(lambda message: message.text == CANCEL_TEXT)
async def cancel_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Создание заявки отменено.", reply_markup=main_menu())


@router.message(lambda message: message.text == "Помощь")
async def help_message(message: Message) -> None:
    await message.answer(HELP, reply_markup=main_menu())


@router.message(lambda message: message.text == "Записаться на встречу")
async def start_booking(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime.now()
    booking_settings = booking_settings_from_app_settings(settings)

    async with session_scope(session_factory) as session:
        closed_days = await ClosedDayRepository(session).list_all()

    closed_dates = {closed_day.day for closed_day in closed_days}
    dates = available_booking_dates(
        now=now,
        closed_dates=closed_dates,
        settings=booking_settings,
    )

    if not dates:
        await message.answer(
            "Сейчас нет доступных дат для записи. Попробуйте позже.",
            reply_markup=main_menu(),
        )
        return

    await state.set_state(BookingFlow.choosing_date)
    await message.answer("Выберите дату встречи.", reply_markup=dates_keyboard(dates))


@router.message(BookingFlow.choosing_date)
async def choose_date(message: Message, state: FSMContext, settings: Settings) -> None:
    selected_date = _parse_date(message.text or "")
    if selected_date is None:
        await message.answer("Выберите дату кнопкой из списка.", reply_markup=cancel_keyboard())
        return

    await state.update_data(date=selected_date.isoformat())
    await state.set_state(BookingFlow.choosing_duration)
    booking_settings = booking_settings_from_app_settings(settings)
    await message.answer(
        "Выберите длительность встречи.",
        reply_markup=durations_keyboard(booking_settings.allowed_durations),
    )


@router.message(BookingFlow.choosing_duration)
async def choose_duration(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    duration = _parse_duration(message.text or "")
    booking_settings = booking_settings_from_app_settings(settings)
    if duration not in booking_settings.allowed_durations:
        await message.answer(
            "Выберите длительность кнопкой из списка.",
            reply_markup=durations_keyboard(booking_settings.allowed_durations),
        )
        return

    data = await state.get_data()
    selected_date = date.fromisoformat(data["date"])
    async with session_scope(session_factory) as session:
        blocking_requests = await BookingRequestRepository(session).list_blocking_for_day(selected_date)

    blocked_intervals = [
        TimeInterval(start=request.start_at, end=request.end_at) for request in blocking_requests
    ]
    slots = generate_slots(
        target_date=selected_date,
        duration_minutes=duration,
        now=datetime.now(),
        blocked_intervals=blocked_intervals,
        settings=booking_settings,
    )

    if not slots:
        await message.answer(
            "На выбранную дату нет свободных слотов. Выберите другую дату.",
            reply_markup=main_menu(),
        )
        await state.clear()
        return

    await state.update_data(duration=duration)
    await state.set_state(BookingFlow.choosing_slot)
    await message.answer("Выберите свободное время.", reply_markup=slots_keyboard(slots))


@router.message(BookingFlow.choosing_slot)
async def choose_slot(message: Message, state: FSMContext, settings: Settings) -> None:
    selected_time = _parse_time(message.text or "")
    if selected_time is None:
        await message.answer("Выберите время кнопкой из списка.", reply_markup=cancel_keyboard())
        return

    data = await state.get_data()
    selected_date = date.fromisoformat(data["date"])
    duration = int(data["duration"])
    start_at = datetime.combine(selected_date, selected_time)
    end_at = start_at + timedelta(minutes=duration)
    booking_settings = booking_settings_from_app_settings(settings)

    if start_at < datetime.now() + timedelta(days=booking_settings.min_notice_days):
        await message.answer(
            "Это время уже недоступно из-за минимального срока записи. Начните запись заново.",
            reply_markup=main_menu(),
        )
        await state.clear()
        return

    await state.update_data(start_at=start_at.isoformat(), end_at=end_at.isoformat())
    await state.set_state(BookingFlow.entering_email)
    await message.answer("Введите email участника встречи.", reply_markup=cancel_keyboard())


@router.message(BookingFlow.entering_email)
async def enter_email(message: Message, state: FSMContext) -> None:
    email = (message.text or "").strip()
    if not is_valid_email(email):
        await message.answer("Email выглядит некорректно. Введите email еще раз.")
        return

    await state.update_data(email=email)
    await state.set_state(BookingFlow.entering_description)
    await message.answer("Введите тему или краткое описание встречи.", reply_markup=cancel_keyboard())


@router.message(BookingFlow.entering_description)
async def enter_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    if not description:
        await message.answer("Описание не должно быть пустым. Введите тему встречи.")
        return

    await state.update_data(description=description)
    data = await state.get_data()
    start_at = datetime.fromisoformat(data["start_at"])
    duration = int(data["duration"])
    summary = (
        "Проверьте заявку:\n\n"
        f"Дата: {start_at.strftime('%d.%m.%Y')}\n"
        f"Время: {start_at.strftime('%H:%M')}\n"
        f"Длительность: {duration} минут\n"
        f"Email: {data['email']}\n"
        f"Описание: {description}\n\n"
        "Если все верно, отправьте заявку на согласование."
    )
    await state.set_state(BookingFlow.confirming)
    await message.answer(summary, reply_markup=confirm_keyboard())


@router.message(BookingFlow.confirming)
async def confirm_booking(
    message: Message,
    state: FSMContext,
    bot: Bot,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if message.text != CONFIRM_TEXT:
        await message.answer("Подтвердите заявку кнопкой или отмените создание.", reply_markup=confirm_keyboard())
        return

    if not message.from_user:
        await message.answer("Не удалось определить пользователя. Начните заново.", reply_markup=main_menu())
        await state.clear()
        return

    data = await state.get_data()
    start_at = datetime.fromisoformat(data["start_at"])
    end_at = datetime.fromisoformat(data["end_at"])
    duration = int(data["duration"])
    email = data["email"]
    description = data["description"]

    async with session_scope(session_factory) as session:
        user = await UserRepository(session).upsert_from_telegram(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username,
            email=email,
        )
        request = await BookingRequestRepository(session).create_pending(
            user_id=user.id,
            start_at=start_at,
            end_at=end_at,
            duration_minutes=duration,
            email=email,
            description=description,
        )

    await state.clear()
    await message.answer(
        "Заявка отправлена на согласование. После решения администратора вы получите уведомление.",
        reply_markup=main_menu(),
    )
    await _notify_admins(bot, settings, request.id, start_at, duration, email, description)


@router.message(lambda message: message.text == "Мои заявки")
async def my_requests(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not message.from_user:
        await message.answer("Не удалось определить пользователя.", reply_markup=main_menu())
        return

    async with session_scope(session_factory) as session:
        user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
        if user is None:
            await message.answer("У вас пока нет заявок.", reply_markup=main_menu())
            return

        requests = await BookingRequestRepository(session).list_by_user(user.id)

    if not requests:
        await message.answer("У вас пока нет заявок.", reply_markup=main_menu())
        return

    lines = ["Ваши заявки:"]
    for request in requests[:10]:
        lines.append(
            f"#{request.id}: {request.start_at.strftime('%d.%m.%Y %H:%M')}, "
            f"{request.duration_minutes} минут, статус: {request.status}"
        )

    await message.answer("\n".join(lines), reply_markup=main_menu())


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(UNKNOWN_ACTION, reply_markup=main_menu())


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


def _parse_time(value: str):
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError:
        return None


async def _notify_admins(
    bot: Bot,
    settings: Settings,
    request_id: int,
    start_at: datetime,
    duration: int,
    email: str,
    description: str,
) -> None:
    if not settings.admin_telegram_ids:
        return

    text = (
        "Новая заявка на встречу:\n\n"
        f"Заявка: #{request_id}\n"
        f"Дата: {start_at.strftime('%d.%m.%Y')}\n"
        f"Время: {start_at.strftime('%H:%M')}\n"
        f"Длительность: {duration} минут\n"
        f"Email: {email}\n"
        f"Описание: {description}\n\n"
        "Подтверждение, перенос и отклонение будут добавлены в админ-сценарии."
    )
    for admin_id in settings.admin_telegram_ids:
        await bot.send_message(admin_id, text)
