from datetime import date
from pathlib import Path

from aiogram import Bot
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot.factory import create_bot
from app.config.settings import Settings, load_settings
from app.db.session import create_app_session_factory
from app.services.mini_app_booking_service import (
    MiniAppBookingError,
    MiniAppBookingPayload,
    booking_request_to_dict,
    create_booking_request_from_mini_app,
    get_booking_dates,
    get_booking_slots,
    list_user_booking_requests,
)
from app.services.telegram_webapp_auth import (
    TelegramWebAppAuthError,
    TelegramWebAppUser,
    validate_telegram_init_data,
)


class BookingRequestIn(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(pattern=r"^\d{2}:\d{2}$")
    duration_minutes: int
    email: str
    description: str


def create_mini_app(
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    bot: Bot | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    session_factory = session_factory or create_app_session_factory(settings)
    bot = bot or create_bot(settings)

    app = FastAPI(title="MeetMaster Mini App API")
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.bot = bot

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    frontend_dir = Path(__file__).resolve().parents[2] / "mini_app" / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=frontend_dir), name="mini-app-static")

        @app.get("/", include_in_schema=False)
        async def index() -> FileResponse:
            return FileResponse(frontend_dir / "index.html")

    async def current_user(
        x_telegram_init_data: str | None = Header(default=None),
    ) -> TelegramWebAppUser:
        if settings.mini_app_dev_mode and settings.mini_app_dev_telegram_id is not None:
            return TelegramWebAppUser(
                id=settings.mini_app_dev_telegram_id,
                first_name="Dev",
                username="dev_user",
            )

        try:
            return validate_telegram_init_data(
                init_data=x_telegram_init_data or "",
                bot_token=settings.bot_token,
            )
        except TelegramWebAppAuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    @app.get("/api/me")
    async def me(user: TelegramWebAppUser = Depends(current_user)) -> dict:
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
        }

    @app.get("/api/booking/dates")
    async def booking_dates() -> dict:
        dates = await get_booking_dates(settings, session_factory)
        return {"dates": [item.isoformat() for item in dates]}

    @app.get("/api/booking/durations")
    async def booking_durations() -> dict:
        return {"durations": list(settings.allowed_durations)}

    @app.get("/api/booking/slots")
    async def booking_slots(target_date: str, duration: int) -> dict:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid date format.") from exc

        try:
            slots = await get_booking_slots(parsed_date, duration, settings, session_factory)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "slots": [
                {
                    "start": start_at.strftime("%H:%M"),
                    "end": end_at.strftime("%H:%M"),
                }
                for start_at, end_at in slots
            ]
        }

    @app.post("/api/booking/requests")
    async def create_booking_request(
        payload: BookingRequestIn,
        user: TelegramWebAppUser = Depends(current_user),
    ) -> dict:
        try:
            request = await create_booking_request_from_mini_app(
                user=user,
                payload=MiniAppBookingPayload(
                    date=payload.date,
                    time=payload.time,
                    duration_minutes=payload.duration_minutes,
                    email=payload.email,
                    description=payload.description,
                ),
                settings=settings,
                session_factory=session_factory,
                bot=bot,
            )
        except MiniAppBookingError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {"request": booking_request_to_dict(request)}

    @app.get("/api/booking/my-requests")
    async def my_requests(user: TelegramWebAppUser = Depends(current_user)) -> dict:
        requests = await list_user_booking_requests(user, session_factory)
        return {"requests": [booking_request_to_dict(request) for request in requests[:20]]}

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await bot.session.close()

    return app


app = create_mini_app()
