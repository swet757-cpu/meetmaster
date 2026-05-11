import json
import urllib.error
import urllib.request

from app.config.settings import load_settings


def main() -> None:
    settings = load_settings()
    if not settings.bot_token:
        print("TELEGRAM_CHECK_OK=False")
        print("ERROR=BOT_TOKEN is empty")
        return

    url = f"https://api.telegram.org/bot{settings.bot_token}/getMe"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {"ok": False, "description": "HTTP error without JSON body"}
    except Exception as exc:
        print("TELEGRAM_CHECK_OK=False")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR_MESSAGE=" + str(exc))
        return

    print("TELEGRAM_CHECK_OK=" + str(bool(data.get("ok"))))
    if data.get("ok"):
        result = data.get("result", {})
        print("BOT_ID=" + str(result.get("id", "")))
        print("BOT_USERNAME=" + str(result.get("username", "")))
        print("BOT_FIRST_NAME=" + str(result.get("first_name", "")))
    else:
        print("ERROR_DESCRIPTION=" + str(data.get("description", "unknown")))


if __name__ == "__main__":
    main()

