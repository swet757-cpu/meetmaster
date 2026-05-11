from dataclasses import dataclass
from datetime import datetime
import asyncio
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config.settings import Settings

GOOGLE_CALENDAR_SCOPES = (
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
)


@dataclass(frozen=True)
class CalendarEventDraft:
    title: str
    description: str
    start_at: datetime
    end_at: datetime
    attendee_email: str


class GoogleCalendarError(RuntimeError):
    pass


class GoogleCalendarNotConfiguredError(GoogleCalendarError):
    pass


class GoogleCalendarClient:
    """Thin async wrapper around the synchronous Google Calendar API client."""

    def __init__(
        self,
        calendar_id: str = "primary",
        token_file: str = "./credentials/google_token.json",
        timezone: str = "Europe/Moscow",
    ) -> None:
        self.calendar_id = calendar_id
        self.token_file = Path(token_file)
        self.timezone = timezone

    async def list_busy_intervals(self, start_at: datetime, end_at: datetime) -> list[tuple[datetime, datetime]]:
        return await asyncio.to_thread(self._list_busy_intervals, start_at, end_at)

    async def create_event(self, draft: CalendarEventDraft) -> str:
        return await asyncio.to_thread(self._create_event, draft)

    async def update_event(self, event_id: str, draft: CalendarEventDraft) -> None:
        await asyncio.to_thread(self._update_event, event_id, draft)

    async def delete_event(self, event_id: str) -> None:
        await asyncio.to_thread(self._delete_event, event_id)

    @classmethod
    def from_settings(cls, settings: Settings) -> "GoogleCalendarClient":
        return cls(
            calendar_id=settings.google_calendar_id,
            token_file=settings.google_oauth_token_file,
            timezone=settings.timezone,
        )

    def _service(self):
        credentials = self._credentials()
        return build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def _credentials(self) -> Credentials:
        if not self.token_file.exists():
            raise GoogleCalendarNotConfiguredError(
                "Google OAuth token file is missing. Run app.tools.google_oauth_setup first."
            )

        try:
            credentials = Credentials.from_authorized_user_file(
                str(self.token_file),
                GOOGLE_CALENDAR_SCOPES,
            )
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self.token_file.write_text(credentials.to_json(), encoding="utf-8")
        except Exception as exc:
            raise GoogleCalendarError("Failed to load or refresh Google OAuth token.") from exc

        if not credentials.valid:
            raise GoogleCalendarNotConfiguredError("Google OAuth token is not valid.")

        return credentials

    def _list_busy_intervals(self, start_at: datetime, end_at: datetime) -> list[tuple[datetime, datetime]]:
        try:
            response = (
                self._service()
                .freebusy()
                .query(
                    body={
                        "timeMin": _google_datetime(start_at, self.timezone),
                        "timeMax": _google_datetime(end_at, self.timezone),
                        "items": [{"id": self.calendar_id}],
                    }
                )
                .execute()
            )
        except Exception as exc:
            raise GoogleCalendarError("Failed to read Google Calendar busy intervals.") from exc
        busy_items = response.get("calendars", {}).get(self.calendar_id, {}).get("busy", [])
        return [
            (_parse_google_datetime(item["start"]), _parse_google_datetime(item["end"]))
            for item in busy_items
        ]

    def _create_event(self, draft: CalendarEventDraft) -> str:
        try:
            response = (
                self._service()
                .events()
                .insert(
                    calendarId=self.calendar_id,
                    body=_event_body(draft, self.timezone),
                    sendUpdates="all",
                )
                .execute()
            )
        except Exception as exc:
            raise GoogleCalendarError("Failed to create Google Calendar event.") from exc
        event_id = response.get("id")
        if not event_id:
            raise GoogleCalendarError("Google Calendar did not return event id.")
        return event_id

    def _update_event(self, event_id: str, draft: CalendarEventDraft) -> None:
        try:
            (
                self._service()
                .events()
                .patch(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    body=_event_body(draft, self.timezone),
                    sendUpdates="all",
                )
                .execute()
            )
        except Exception as exc:
            raise GoogleCalendarError("Failed to update Google Calendar event.") from exc

    def _delete_event(self, event_id: str) -> None:
        try:
            (
                self._service()
                .events()
                .delete(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    sendUpdates="all",
                )
                .execute()
            )
        except Exception as exc:
            raise GoogleCalendarError("Failed to delete Google Calendar event.") from exc


def _event_body(draft: CalendarEventDraft, timezone: str) -> dict:
    return {
        "summary": draft.title,
        "description": draft.description,
        "start": {"dateTime": _google_datetime(draft.start_at, timezone), "timeZone": timezone},
        "end": {"dateTime": _google_datetime(draft.end_at, timezone), "timeZone": timezone},
        "attendees": [{"email": draft.attendee_email}],
    }


def _google_datetime(value: datetime, timezone: str) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo(timezone))
    return value.isoformat()


def _parse_google_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return parsed.replace(tzinfo=None)
