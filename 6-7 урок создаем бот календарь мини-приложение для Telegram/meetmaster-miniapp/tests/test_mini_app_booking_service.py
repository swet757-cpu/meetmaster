from datetime import datetime, time
import unittest

from app.config.settings import Settings
from app.db.models import Base, RequestStatus
from app.db.session import create_engine, create_session_factory
from app.services.mini_app_booking_service import (
    MiniAppBookingError,
    MiniAppBookingPayload,
    create_booking_request_from_mini_app,
    get_booking_slots,
    list_user_booking_requests,
)
from app.services.telegram_webapp_auth import TelegramWebAppUser


class MiniAppBookingServiceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = create_session_factory(self.engine)
        self.settings = Settings(
            bot_token="token",
            admin_telegram_ids=(111,),
            telegram_force_ipv4=True,
            database_url="sqlite+aiosqlite:///:memory:",
            google_calendar_enabled=False,
            google_calendar_id="primary",
            google_oauth_client_secret_file="./credentials/google_client_secret.json",
            google_oauth_token_file="./credentials/google_token.json",
            timezone="Europe/Moscow",
            workday_start=time(9, 0),
            workday_end=time(17, 0),
            min_notice_days=1,
            buffer_minutes=15,
            allowed_durations=(30, 45, 60),
            log_level="INFO",
            mini_app_dev_mode=False,
            mini_app_dev_telegram_id=None,
            mini_app_url="",
        )

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_create_booking_from_mini_app(self) -> None:
        user = TelegramWebAppUser(id=8695348072, first_name="Anna", username="anna")
        request = await create_booking_request_from_mini_app(
            user=user,
            payload=MiniAppBookingPayload(
                date="2026-05-19",
                time="09:45",
                duration_minutes=45,
                email="client@example.com",
                description="Мини-приложение",
            ),
            settings=self.settings,
            session_factory=self.session_factory,
            now=datetime(2026, 5, 14, 9, 0),
        )

        self.assertEqual(request.status, RequestStatus.PENDING_APPROVAL.value)
        self.assertEqual(request.start_at, datetime(2026, 5, 19, 9, 45))

        requests = await list_user_booking_requests(user, self.session_factory)
        self.assertEqual([item.id for item in requests], [request.id])

    async def test_busy_slot_is_rejected(self) -> None:
        user = TelegramWebAppUser(id=1001, first_name="Busy")
        await create_booking_request_from_mini_app(
            user=user,
            payload=MiniAppBookingPayload(
                date="2026-05-19",
                time="09:45",
                duration_minutes=45,
                email="first@example.com",
                description="Первая встреча",
            ),
            settings=self.settings,
            session_factory=self.session_factory,
            now=datetime(2026, 5, 14, 9, 0),
        )

        with self.assertRaises(MiniAppBookingError):
            await create_booking_request_from_mini_app(
                user=TelegramWebAppUser(id=1002, first_name="Second"),
                payload=MiniAppBookingPayload(
                    date="2026-05-19",
                    time="09:45",
                    duration_minutes=45,
                    email="second@example.com",
                    description="Вторая встреча",
                ),
                settings=self.settings,
                session_factory=self.session_factory,
                now=datetime(2026, 5, 14, 9, 0),
            )

    async def test_slots_use_existing_blocking_requests(self) -> None:
        user = TelegramWebAppUser(id=1003, first_name="Slots")
        await create_booking_request_from_mini_app(
            user=user,
            payload=MiniAppBookingPayload(
                date="2026-05-19",
                time="10:00",
                duration_minutes=30,
                email="client@example.com",
                description="Занятый слот",
            ),
            settings=self.settings,
            session_factory=self.session_factory,
            now=datetime(2026, 5, 14, 9, 0),
        )

        slots = await get_booking_slots(
            target_date=datetime(2026, 5, 19).date(),
            duration_minutes=30,
            settings=self.settings,
            session_factory=self.session_factory,
            now=datetime(2026, 5, 14, 9, 0),
        )
        starts = {start.strftime("%H:%M") for start, _ in slots}

        self.assertNotIn("09:45", starts)
        self.assertNotIn("10:00", starts)
        self.assertNotIn("10:15", starts)
        self.assertIn("10:45", starts)

    async def test_invalid_email_is_rejected(self) -> None:
        with self.assertRaises(MiniAppBookingError):
            await create_booking_request_from_mini_app(
                user=TelegramWebAppUser(id=1004),
                payload=MiniAppBookingPayload(
                    date="2026-05-19",
                    time="09:45",
                    duration_minutes=45,
                    email="bad-email",
                    description="Описание",
                ),
                settings=self.settings,
                session_factory=self.session_factory,
                now=datetime(2026, 5, 14, 9, 0),
            )


if __name__ == "__main__":
    unittest.main()
