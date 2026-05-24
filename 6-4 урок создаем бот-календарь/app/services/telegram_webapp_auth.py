from dataclasses import dataclass
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


class TelegramWebAppAuthError(ValueError):
    pass


@dataclass(frozen=True)
class TelegramWebAppUser:
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


def validate_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 86400,
    now: int | None = None,
) -> TelegramWebAppUser:
    if not init_data:
        raise TelegramWebAppAuthError("Telegram initData is missing.")
    if not bot_token:
        raise TelegramWebAppAuthError("Bot token is not configured.")

    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", None)
    if not received_hash:
        raise TelegramWebAppAuthError("Telegram initData hash is missing.")

    data_check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    expected_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise TelegramWebAppAuthError("Telegram initData hash is invalid.")

    auth_date = _parse_auth_date(values.get("auth_date"))
    current_time = int(time.time()) if now is None else now
    if max_age_seconds > 0 and current_time - auth_date > max_age_seconds:
        raise TelegramWebAppAuthError("Telegram initData is expired.")

    raw_user = values.get("user")
    if not raw_user:
        raise TelegramWebAppAuthError("Telegram initData user is missing.")

    try:
        user_data = json.loads(raw_user)
        telegram_id = int(user_data["id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise TelegramWebAppAuthError("Telegram initData user is invalid.") from exc

    return TelegramWebAppUser(
        id=telegram_id,
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        username=user_data.get("username"),
    )


def _parse_auth_date(value: str | None) -> int:
    if value is None:
        raise TelegramWebAppAuthError("Telegram initData auth_date is missing.")
    try:
        return int(value)
    except ValueError as exc:
        raise TelegramWebAppAuthError("Telegram initData auth_date is invalid.") from exc
