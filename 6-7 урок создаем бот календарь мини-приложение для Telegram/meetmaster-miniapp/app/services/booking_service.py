from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class BookingStatus(StrEnum):
    NEW = "new"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DECLINED = "declined"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class BookingDraft:
    telegram_user_id: int
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    email: str
    description: str


def initial_status() -> BookingStatus:
    return BookingStatus.PENDING_APPROVAL

