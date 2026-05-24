import socket

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from app.config.settings import Settings


def create_bot(settings: Settings) -> Bot:
    session = AiohttpSession()
    if settings.telegram_force_ipv4:
        session._connector_init["family"] = socket.AF_INET

    return Bot(token=settings.bot_token, session=session)

