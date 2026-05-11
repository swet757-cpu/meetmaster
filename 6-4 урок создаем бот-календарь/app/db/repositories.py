from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BookingRequest, ClosedDay, RequestStatus, Setting, StatusHistory, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def upsert_from_telegram(
        self,
        telegram_id: int,
        first_name: str | None,
        last_name: str | None,
        username: str | None,
        email: str | None = None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        now = datetime.utcnow()
        if user is None:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                created_at=now,
                updated_at=now,
            )
            self.session.add(user)
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            if email is not None:
                user.email = email
            user.updated_at = now

        await self.session.flush()
        return user


class BookingRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_pending(
        self,
        user_id: int,
        start_at: datetime,
        end_at: datetime,
        duration_minutes: int,
        email: str,
        description: str,
    ) -> BookingRequest:
        request = BookingRequest(
            user_id=user_id,
            start_at=start_at,
            end_at=end_at,
            duration_minutes=duration_minutes,
            email=email,
            description=description,
            status=RequestStatus.PENDING_APPROVAL.value,
        )
        self.session.add(request)
        await self.session.flush()
        await self.add_status_history(
            booking_request_id=request.id,
            old_status=None,
            new_status=request.status,
            comment="Заявка создана пользователем.",
        )
        return request

    async def get_by_id(self, request_id: int) -> BookingRequest | None:
        result = await self.session.execute(
            select(BookingRequest).where(BookingRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def list_pending(self) -> list[BookingRequest]:
        result = await self.session.execute(
            select(BookingRequest)
            .where(BookingRequest.status == RequestStatus.PENDING_APPROVAL.value)
            .order_by(BookingRequest.start_at)
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_id: int) -> list[BookingRequest]:
        result = await self.session.execute(
            select(BookingRequest)
            .where(BookingRequest.user_id == user_id)
            .order_by(BookingRequest.start_at.desc())
        )
        return list(result.scalars().all())

    async def list_blocking_for_day(self, day: date) -> list[BookingRequest]:
        day_start = datetime.combine(day, time.min)
        day_end = datetime.combine(day, time.max)
        blocking_statuses = (
            RequestStatus.PENDING_APPROVAL.value,
            RequestStatus.APPROVED.value,
            RequestStatus.RESCHEDULED.value,
        )
        result = await self.session.execute(
            select(BookingRequest)
            .where(BookingRequest.start_at >= day_start)
            .where(BookingRequest.start_at <= day_end)
            .where(BookingRequest.status.in_(blocking_statuses))
            .order_by(BookingRequest.start_at)
        )
        return list(result.scalars().all())

    async def change_status(
        self,
        request: BookingRequest,
        new_status: RequestStatus,
        comment: str | None = None,
    ) -> BookingRequest:
        old_status = request.status
        request.status = new_status.value
        request.updated_at = datetime.utcnow()
        await self.add_status_history(
            booking_request_id=request.id,
            old_status=old_status,
            new_status=request.status,
            comment=comment,
        )
        await self.session.flush()
        return request

    async def add_status_history(
        self,
        booking_request_id: int,
        old_status: str | None,
        new_status: str,
        comment: str | None,
    ) -> StatusHistory:
        history = StatusHistory(
            booking_request_id=booking_request_id,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
        )
        self.session.add(history)
        await self.session.flush()
        return history


class ClosedDayRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, day: date, reason: str | None = None) -> ClosedDay:
        existing = await self.get(day)
        if existing is not None:
            existing.reason = reason
            return existing

        closed_day = ClosedDay(day=day, reason=reason)
        self.session.add(closed_day)
        await self.session.flush()
        return closed_day

    async def get(self, day: date) -> ClosedDay | None:
        result = await self.session.execute(select(ClosedDay).where(ClosedDay.day == day))
        return result.scalar_one_or_none()

    async def remove(self, day: date) -> bool:
        closed_day = await self.get(day)
        if closed_day is None:
            return False

        await self.session.delete(closed_day)
        await self.session.flush()
        return True

    async def list_all(self) -> list[ClosedDay]:
        result = await self.session.execute(select(ClosedDay).order_by(ClosedDay.day))
        return list(result.scalars().all())


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def set(self, key: str, value: str) -> Setting:
        setting = await self.get(key)
        now = datetime.utcnow()
        if setting is None:
            setting = Setting(key=key, value=value, updated_at=now)
            self.session.add(setting)
        else:
            setting.value = value
            setting.updated_at = now

        await self.session.flush()
        return setting

    async def get(self, key: str) -> Setting | None:
        result = await self.session.execute(select(Setting).where(Setting.key == key))
        return result.scalar_one_or_none()
