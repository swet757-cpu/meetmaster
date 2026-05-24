import hashlib
import hmac
import json
import unittest
from urllib.parse import urlencode

from app.services.telegram_webapp_auth import (
    TelegramWebAppAuthError,
    validate_telegram_init_data,
)


class TelegramWebAppAuthTest(unittest.TestCase):
    def test_valid_init_data_returns_user(self) -> None:
        bot_token = "123456:ABCDEF"
        init_data = _signed_init_data(
            bot_token=bot_token,
            values={
                "auth_date": "1000",
                "query_id": "abc",
                "user": json.dumps(
                    {
                        "id": 8695348072,
                        "first_name": "Anna",
                        "username": "anna",
                    },
                    separators=(",", ":"),
                ),
            },
        )

        user = validate_telegram_init_data(
            init_data,
            bot_token=bot_token,
            now=1001,
        )

        self.assertEqual(user.id, 8695348072)
        self.assertEqual(user.first_name, "Anna")
        self.assertEqual(user.username, "anna")

    def test_invalid_hash_is_rejected(self) -> None:
        init_data = _signed_init_data(
            bot_token="123456:ABCDEF",
            values={
                "auth_date": "1000",
                "user": json.dumps({"id": 1}, separators=(",", ":")),
            },
        )

        with self.assertRaises(TelegramWebAppAuthError):
            validate_telegram_init_data(
                init_data.replace("hash=", "hash=bad"),
                bot_token="123456:ABCDEF",
                now=1001,
            )

    def test_expired_init_data_is_rejected(self) -> None:
        init_data = _signed_init_data(
            bot_token="123456:ABCDEF",
            values={
                "auth_date": "1000",
                "user": json.dumps({"id": 1}, separators=(",", ":")),
            },
        )

        with self.assertRaises(TelegramWebAppAuthError):
            validate_telegram_init_data(
                init_data,
                bot_token="123456:ABCDEF",
                now=1000 + 86401,
            )


def _signed_init_data(bot_token: str, values: dict[str, str]) -> str:
    data_check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return urlencode({**values, "hash": signature})


if __name__ == "__main__":
    unittest.main()
