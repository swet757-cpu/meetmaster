from datetime import date, datetime
import unittest

from sqlalchemy import select

from app.db.models import Base, RequestStatus, StatusHistory
from app.db.repositories import (
    BookingRequestRepository,
    ClosedDayRepository,
    SettingsRepository,
    UserRepository,
)
from app.db.session import create_engine, create_session_factory, session_scope


class RepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = create_session_factory(self.engine)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_create_user_and_pending_booking_request(self) -> None:
        async with session_scope(self.session_factory) as session:
            user_repo = UserRepository(session)
            request_repo = BookingRequestRepository(session)

            user = await user_repo.upsert_from_telegram(
                telegram_id=1001,
                first_name="Анна",
                last_name=None,
                username="anna",
                email="anna@example.com",
            )
            request = await request_repo.create_pending(
                user_id=user.id,
                start_at=datetime(2026, 5, 13, 9, 0),
                end_at=datetime(2026, 5, 13, 9, 30),
                duration_minutes=30,
                email="client@example.com",
                description="Тестовая встреча",
            )

            self.assertEqual(request.status, RequestStatus.PENDING_APPROVAL.value)

        async with session_scope(self.session_factory) as session:
            request_repo = BookingRequestRepository(session)
            pending = await request_repo.list_pending()
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0].email, "client@example.com")

            histories = (await session.execute(select(StatusHistory))).scalars().all()
            self.assertEqual(len(histories), 1)
            self.assertEqual(histories[0].new_status, RequestStatus.PENDING_APPROVAL.value)

    async def test_change_booking_request_status(self) -> None:
        async with session_scope(self.session_factory) as session:
            user = await UserRepository(session).upsert_from_telegram(
                telegram_id=1002,
                first_name="User",
                last_name=None,
                username=None,
            )
            request_repo = BookingRequestRepository(session)
            request = await request_repo.create_pending(
                user_id=user.id,
                start_at=datetime(2026, 5, 13, 10, 0),
                end_at=datetime(2026, 5, 13, 10, 30),
                duration_minutes=30,
                email="client@example.com",
                description="Тест",
            )
            await request_repo.change_status(
                request=request,
                new_status=RequestStatus.APPROVED,
                comment="Подтверждено администратором.",
            )

        async with session_scope(self.session_factory) as session:
            request = await BookingRequestRepository(session).get_by_id(1)
            self.assertIsNotNone(request)
            self.assertEqual(request.status, RequestStatus.APPROVED.value)

            histories = (await session.execute(select(StatusHistory))).scalars().all()
            self.assertEqual(len(histories), 2)
            self.assertEqual(histories[-1].old_status, RequestStatus.PENDING_APPROVAL.value)
            self.assertEqual(histories[-1].new_status, RequestStatus.APPROVED.value)

    async def test_list_by_user_and_blocking_for_day(self) -> None:
        async with session_scope(self.session_factory) as session:
            user_repo = UserRepository(session)
            request_repo = BookingRequestRepository(session)
            first_user = await user_repo.upsert_from_telegram(
                telegram_id=2001,
                first_name="First",
                last_name=None,
                username=None,
            )
            second_user = await user_repo.upsert_from_telegram(
                telegram_id=2002,
                first_name="Second",
                last_name=None,
                username=None,
            )
            first_request = await request_repo.create_pending(
                user_id=first_user.id,
                start_at=datetime(2026, 5, 13, 9, 0),
                end_at=datetime(2026, 5, 13, 9, 30),
                duration_minutes=30,
                email="first@example.com",
                description="Первая встреча",
            )
            second_request = await request_repo.create_pending(
                user_id=second_user.id,
                start_at=datetime(2026, 5, 13, 11, 0),
                end_at=datetime(2026, 5, 13, 11, 30),
                duration_minutes=30,
                email="second@example.com",
                description="Вторая встреча",
            )
            await request_repo.change_status(
                request=second_request,
                new_status=RequestStatus.CANCELLED,
                comment="Отменено.",
            )

        async with session_scope(self.session_factory) as session:
            request_repo = BookingRequestRepository(session)
            user_requests = await request_repo.list_by_user(first_user.id)
            blocking = await request_repo.list_blocking_for_day(date(2026, 5, 13))

            self.assertEqual([request.id for request in user_requests], [first_request.id])
            self.assertEqual([request.id for request in blocking], [first_request.id])

    async def test_closed_day_repository(self) -> None:
        target_day = date(2026, 5, 15)

        async with session_scope(self.session_factory) as session:
            repo = ClosedDayRepository(session)
            await repo.add(target_day, reason="Личный день")
            closed_days = await repo.list_all()
            self.assertEqual(len(closed_days), 1)
            self.assertEqual(closed_days[0].day, target_day)

        async with session_scope(self.session_factory) as session:
            repo = ClosedDayRepository(session)
            removed = await repo.remove(target_day)
            self.assertTrue(removed)
            self.assertEqual(await repo.list_all(), [])

    async def test_settings_repository(self) -> None:
        async with session_scope(self.session_factory) as session:
            repo = SettingsRepository(session)
            await repo.set("buffer_minutes", "15")
            await repo.set("buffer_minutes", "20")
            setting = await repo.get("buffer_minutes")

            self.assertIsNotNone(setting)
            self.assertEqual(setting.value, "20")


if __name__ == "__main__":
    unittest.main()
