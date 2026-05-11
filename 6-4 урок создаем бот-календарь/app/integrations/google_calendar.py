from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CalendarEventDraft:
    title: str
    description: str
    start_at: datetime
    end_at: datetime
    attendee_email: str


class GoogleCalendarClient:
    """Thin wrapper for Google Calendar API.

    Real OAuth and API calls are implemented after credentials are prepared.
    """

    def __init__(self, calendar_id: str = "primary") -> None:
        self.calendar_id = calendar_id

    async def list_busy_intervals(self, start_at: datetime, end_at: datetime) -> list[tuple[datetime, datetime]]:
        raise NotImplementedError("Google Calendar integration will be added after OAuth setup.")

    async def create_event(self, draft: CalendarEventDraft) -> str:
        raise NotImplementedError("Google Calendar integration will be added after OAuth setup.")

