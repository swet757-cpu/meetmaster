from dataclasses import dataclass
from datetime import date, datetime, timedelta

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot.keyboards import admin_request_actions_keyboard
from app.config.settings import Settings
from app.db.models import BookingRequest, RequestStatus
from app.db.repositories import BookingRequestRepository, ClosedDayRepository, UserRepository
from app.db.session import session_scope
from app.services.email_validator import is_valid_email
from app.services.slot_service import (
    TimeInterval,
    available_booking_dates,
    booking_settings_from_app_settings,
    generate_slots,
)
from app.services.telegram_webapp_auth import TelegramWebAppUser


class MiniAppBookingError(ValueError):
    pass


@dataclass(frozen=True)
class MiniAppBookingPayload:
    date: str
    time: str
    duration_minutes: int
    email: str
    description: str


async def get_booking_dates(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    now: datetime | None = None,
) -> list[date]:
    booking_settings = booking_settings_from_app_settings(settings)
    async with session_scope(session_factory) as session:
        closed_days = await ClosedDayRepository(session).list_all()

    return available_booking_dates(
        now=now or datetime.now(),
        closed_dates={closed_day.day for closed_day in closed_days},
        settings=booking_settings,
    )


async def get_booking_slots(
    target_date: date,
    duration_minutes: int,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    now: datetime | None = None,
) -> list[tuple[datetime, datetime]]:
    booking_settings = booking_settings_from_app_settings(settings)
    async with session_scope(session_factory) as session:
        blocking_requests = await BookingRequestRepository(session).list_blocking_for_day(target_date)

    slots = generate_slots(
        target_date=target_date,
        duration_minutes=duration_minutes,
        now=now or datetime.now(),
        blocked_intervals=[
            TimeInterval(start=request.start_at, end=request.end_at)
            for request in blocking_requests
        ],
        settings=booking_settings,
    )
    return [(slot.start, slot.end) for slot in slots]


async def create_booking_request_from_mini_app(
    user: TelegramWebAppUser,
    payload: MiniAppBookingPayload,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    bot: Bot | None = None,
    now: datetime | None = None,
) -> BookingRequest:
    email = payload.email.strip()
    description = payload.description.strip()
    if not is_valid_email(email):
        raise MiniAppBookingError("Email is invalid.")
    if not description:
        raise MiniAppBookingError("Description is required.")
    if payload.duration_minutes not in settings.allowed_durations:
        raise MiniAppBookingError("Meeting duration is not allowed.")

    try:
        selected_date = date.fromisoformat(payload.date)
        selected_time = datetime.strptime(payload.time, "%H:%M").time()
    except ValueError as exc:
        raise MiniAppBookingError("Date or time format is invalid.") from exc

    start_at = datetime.combine(selected_date, selected_time)
    end_at = start_at + timedelta(minutes=payload.duration_minutes)
    available_slots = await get_booking_slots(
        target_date=selected_date,
        duration_minutes=payload.duration_minutes,
        settings=settings,
        session_factory=session_factory,
        now=now,
    )
    if start_at not in {slot_start for slot_start, _ in available_slots}:
        raise MiniAppBookingError("Selected slot is no longer available.")

    async with session_scope(session_factory) as session:
        db_user = await UserRepository(session).upsert_from_telegram(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=email,
        )
        request = await BookingRequestRepository(session).create_pending(
            user_id=db_user.id,
            start_at=start_at,
            end_at=end_at,
            duration_minutes=payload.duration_minutes,
            email=email,
            description=description,
        )

    if bot is not None:
        await notify_admins_about_mini_app_request(bot, settings, request)

    return request


async def list_user_booking_requests(
    user: TelegramWebAppUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> list[BookingRequest]:
    async with session_scope(session_factory) as session:
        db_user = await UserRepository(session).get_by_telegram_id(user.id)
        if db_user is None:
            return []
        return await BookingRequestRepository(session).list_by_user(db_user.id)


async def notify_admins_about_mini_app_request(
    bot: Bot,
    settings: Settings,
    request: BookingRequest,
) -> None:
    if not settings.admin_telegram_ids:
        return

    text = (
        "Новая заявка на встречу из Mini App:\n\n"
        f"Заявка: #{request.id}\n"
        f"Дата: {request.start_at.strftime('%d.%m.%Y')}\n"
        f"Время: {request.start_at.strftime('%H:%M')}\n"
        f"Длительность: {request.duration_minutes} минут\n"
        f"Email: {request.email}\n"
        f"Описание: {request.description}\n\n"
        "Выберите действие кнопкой ниже."
    )
    for admin_id in settings.admin_telegram_ids:
        await bot.send_message(
            admin_id,
            text,
            reply_markup=admin_request_actions_keyboard(request.id),
        )


def booking_request_to_dict(request: BookingRequest) -> dict:
    return {
        "id": request.id,
        "date": request.start_at.date().isoformat(),
        "time": request.start_at.strftime("%H:%M"),
        "duration_minutes": request.duration_minutes,
        "email": request.email,
        "description": request.description,
        "status": request.status,
        "status_label": _status_label(request.status),
    }


def _status_label(status: str) -> str:
    labels = {
        RequestStatus.PENDING_APPROVAL.value: "на согласовании",
        RequestStatus.APPROVED.value: "подтверждена",
        RequestStatus.DECLINED.value: "отклонена",
        RequestStatus.CANCELLED.value: "отменена",
        RequestStatus.RESCHEDULED.value: "перенесена",
    }
    return labels.get(status, status)
