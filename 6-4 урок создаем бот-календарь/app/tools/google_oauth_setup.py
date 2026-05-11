from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from app.config.settings import load_settings
from app.integrations.google_calendar import GOOGLE_CALENDAR_SCOPES


def main() -> None:
    settings = load_settings()
    client_secret_file = Path(settings.google_oauth_client_secret_file)
    token_file = Path(settings.google_oauth_token_file)

    if not client_secret_file.exists():
        raise FileNotFoundError(
            f"Google OAuth client secret file was not found: {client_secret_file}"
        )

    token_file.parent.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secret_file),
        scopes=GOOGLE_CALENDAR_SCOPES,
    )
    credentials = flow.run_local_server(port=0)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    print(f"Google OAuth token saved to {token_file}")


if __name__ == "__main__":
    main()
