from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.config.settings import Settings


@dataclass(frozen=True)
class BookingSettings:
    workday_start: time = time(9, 0)
    workday_end: time = time(17, 0)
    workdays: tuple[int, ...] = (0, 1, 2, 3, 4)
    min_notice_days: int = 1
    buffer_minutes: int = 15
    allowed_durations: tuple[int, ...] = (30, 45, 60)
    slot_step_minutes: int = 15


@dataclass(frozen=True)
class TimeInterval:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class Slot:
    start: datetime
    end: datetime


class SlotRuleError(ValueError):
    pass


def booking_settings_from_app_settings(settings: Settings) -> BookingSettings:
    return BookingSettings(
        workday_start=settings.workday_start,
        workday_end=settings.workday_end,
        min_notice_days=settings.min_notice_days,
        buffer_minutes=settings.buffer_minutes,
        allowed_durations=settings.allowed_durations,
    )


def available_booking_dates(
    now: datetime,
    closed_dates: set[date] | None = None,
    settings: BookingSettings | None = None,
    days_ahead: int = 14,
) -> list[date]:
    settings = settings or BookingSettings()
    closed_dates = closed_dates or set()
    dates: list[date] = []
    start_date = (now + timedelta(days=settings.min_notice_days)).date()

    for offset in range(days_ahead + 1):
        candidate = start_date + timedelta(days=offset)
        if is_working_day(candidate, settings) and not is_closed_day(candidate, closed_dates):
            dates.append(candidate)

    return dates


def is_working_day(target_date: date, settings: BookingSettings) -> bool:
    return target_date.weekday() in settings.workdays


def is_closed_day(target_date: date, closed_dates: set[date]) -> bool:
    return target_date in closed_dates


def generate_slots(
    target_date: date,
    duration_minutes: int,
    now: datetime,
    busy_intervals: list[TimeInterval] | None = None,
    blocked_intervals: list[TimeInterval] | None = None,
    closed_dates: set[date] | None = None,
    settings: BookingSettings | None = None,
) -> list[Slot]:
    settings = settings or BookingSettings()
    busy_intervals = busy_intervals or []
    blocked_intervals = blocked_intervals or []
    closed_dates = closed_dates or set()

    if duration_minutes not in settings.allowed_durations:
        raise SlotRuleError("Недоступная длительность встречи.")

    if not is_working_day(target_date, settings):
        return []

    if is_closed_day(target_date, closed_dates):
        return []

    day_start = datetime.combine(target_date, settings.workday_start)
    day_end = datetime.combine(target_date, settings.workday_end)
    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=settings.slot_step_minutes)
    min_start = now + timedelta(days=settings.min_notice_days)

    slots: list[Slot] = []
    candidate_start = day_start
    intervals = [*busy_intervals, *blocked_intervals]

    while candidate_start + duration <= day_end:
        candidate = Slot(start=candidate_start, end=candidate_start + duration)
        if candidate.start >= min_start and not _overlaps_with_buffer(candidate, intervals, settings):
            slots.append(candidate)
        candidate_start += step

    return slots


def _overlaps_with_buffer(
    slot: Slot,
    intervals: list[TimeInterval],
    settings: BookingSettings,
) -> bool:
    buffer_delta = timedelta(minutes=settings.buffer_minutes)
    for interval in intervals:
        protected_start = interval.start - buffer_delta
        protected_end = interval.end + buffer_delta
        if slot.start < protected_end and slot.end > protected_start:
            return True
    return False
