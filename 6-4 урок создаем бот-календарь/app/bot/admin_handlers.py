from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot.keyboards import (
    APPROVE_ACTION,
    CANCEL_ACTION,
    DECLINE_ACTION,
    admin_menu,
    admin_request_actions_keyboard,
)
from app.bot.messages import ADMIN_ONLY
from app.config.settings import Settings
from app.db.models import RequestStatus
from app.db.repositories import BookingRequestRepository, UserRepository
from app.db.session import session_scope

router = Router()


def _is_admin(telegram_id: int, settings: Settings) -> bool:
    return telegram_id in settings.admin_telegram_ids


@router.message(Command("admin"))
async def admin(message: Message, settings: Settings) -> None:
    if not message.from_user or not _is_admin(message.from_user.id, settings):
        await message.answer(ADMIN_ONLY)
        return

    await message.answer("Админ-меню MeetMaster.", reply_markup=admin_menu())


@router.message(Command("admin_requests"))
@router.message(lambda message: message.text == "Заявки на согласовании")
async def pending_requests(
    message: Message,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not message.from_user or not _is_admin(message.from_user.id, settings):
        await message.answer(ADMIN_ONLY)
        return

    async with session_scope(session_factory) as session:
        requests = await BookingRequestRepository(session).list_pending()

    if not requests:
        await message.answer("Заявок на согласовании нет.", reply_markup=admin_menu())
        return

    await message.answer("Заявки на согласовании:", reply_markup=admin_menu())
    for request in requests[:10]:
        await message.answer(
            _admin_request_message(request),
            reply_markup=admin_request_actions_keyboard(request.id),
        )


@router.callback_query(lambda query: bool(query.data and query.data.startswith("request:")))
async def handle_request_action(
    query: CallbackQuery,
    bot: Bot,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not query.from_user or not _is_admin(query.from_user.id, settings):
        await query.answer(ADMIN_ONLY, show_alert=True)
        return

    action, request_id = _parse_request_callback(query.data or "")
    if action is None or request_id is None:
        await query.answer("Не удалось обработать действие.", show_alert=True)
        return

    status_by_action = {
        APPROVE_ACTION: RequestStatus.APPROVED,
        DECLINE_ACTION: RequestStatus.DECLINED,
        CANCEL_ACTION: RequestStatus.CANCELLED,
    }
    new_status = status_by_action.get(action)
    if new_status is None:
        await query.answer("Действие пока не поддерживается.", show_alert=True)
        return

    async with session_scope(session_factory) as session:
        request_repo = BookingRequestRepository(session)
        user_repo = UserRepository(session)
        request = await request_repo.get_by_id(request_id)
        if request is None:
            await query.answer("Заявка не найдена.", show_alert=True)
            return

        if request.status != RequestStatus.PENDING_APPROVAL.value:
            await query.answer("Заявка уже обработана.", show_alert=True)
            return

        await request_repo.change_status(
            request=request,
            new_status=new_status,
            comment=f"Администратор выполнил действие: {action}.",
        )
        user = await user_repo.get_by_id(request.user_id)

    if user is not None:
        await bot.send_message(
            user.telegram_id,
            _user_status_message(new_status, request.start_at),
        )

    if query.message:
        await query.message.edit_text(
            f"{query.message.text}\n\nСтатус изменен: {_status_label(new_status)}"
        )
    await query.answer("Готово.")


def _parse_request_callback(data: str) -> tuple[str | None, int | None]:
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "request":
        return None, None
    try:
        return parts[1], int(parts[2])
    except ValueError:
        return None, None


def _status_label(status: RequestStatus) -> str:
    labels = {
        RequestStatus.APPROVED: "подтверждена",
        RequestStatus.DECLINED: "отклонена",
        RequestStatus.CANCELLED: "отменена",
    }
    return labels.get(status, status.value)


def _admin_request_message(request) -> str:
    return (
        "Заявка на встречу:\n\n"
        f"Заявка: #{request.id}\n"
        f"Дата: {request.start_at.strftime('%d.%m.%Y')}\n"
        f"Время: {request.start_at.strftime('%H:%M')}\n"
        f"Длительность: {request.duration_minutes} минут\n"
        f"Email: {request.email}\n"
        f"Описание: {request.description}"
    )


def _user_status_message(status: RequestStatus, start_at) -> str:
    if status == RequestStatus.APPROVED:
        return (
            "Ваша заявка подтверждена.\n\n"
            f"Дата и время: {start_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            "Добавление в Google Календарь будет подключено следующим этапом."
        )
    if status == RequestStatus.DECLINED:
        return "Ваша заявка отклонена. Можно выбрать другой слот."
    if status == RequestStatus.CANCELLED:
        return "Ваша заявка отменена администратором."
    return "Статус вашей заявки изменен."
